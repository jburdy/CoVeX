"""
Orchestre l'analyse metier et expose la route FastAPI `POST /analyze`.

Usage:
- Module importe par `backend/src/main.py` pour enregistrer le routeur API.
- Reutilise par `tools/research/select_engines_by_cost_score.py` pour appeler l'analyse hors HTTP.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol, cast

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from analysis_profiles_config import AnalysisProfileRuntime, load_runtime_analysis_profiles
from inference import infer, InferenceClientUnavailableError, load_inference_engines_config
from settings import APP_LOGGER_NAME, get_prompt_trace_logger, should_emit_prompt_trace

logger = logging.getLogger(APP_LOGGER_NAME)
router = APIRouter(tags=["analysis"])

Decision = Literal["KO", "PARTIEL", "OK"]


class ProfileNotFoundError(ValueError):
    pass


class AnalysisServiceUnavailableError(RuntimeError):
    pass


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    inference_engine: str | None = Field(default=None, min_length=1)


class AnalyzeResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    decision: Decision
    justification: str = Field(min_length=1)
    profile_used: str = Field(min_length=1)
    latency_sec: float | None = Field(default=None, ge=0.0)
    model_used: str | None = Field(default=None, min_length=1)
    covered_elements: list[str] = Field(default_factory=list)
    missing_elements: list[str] = Field(default_factory=list)
    extractions: list[dict] = Field(default_factory=list)


@dataclass(frozen=True)
class AnalysisResult:
    score: int
    decision: Decision
    justification: str
    profile_used: str
    latency_sec: float | None = None
    model_used: str | None = None
    covered_elements: list[str] = field(default_factory=list)
    missing_elements: list[str] = field(default_factory=list)
    extractions: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ResolvedAnalysisContext:
    profile: AnalysisProfileRuntime
    inference_engine_key: str


class _InferenceAdapter(Protocol):
    def infer(self, **kwargs: object) -> dict[str, object]: ...


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _as_dict_list(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_optional_float(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _as_optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _as_optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _format_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _format_json_compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _build_trace_message(
    *,
    profile_id: str,
    text: str,
    trace_payload: dict[str, object],
    result: AnalysisResult,
) -> str:
    coverage_item_prompt = _as_optional_str(trace_payload.get("coverage_item_prompt")) or ""
    llm_instruction = _as_optional_str(trace_payload.get("llm_instruction_sent")) or ""
    raw_response_keys = trace_payload.get("raw_inference_engine_response_keys", [])
    raw_response = trace_payload.get("raw_inference_engine_response", {})
    visualization_html = trace_payload.get("visualization_html", {})
    llm_response = trace_payload.get("llm_response_received", {})
    extraction_result = trace_payload.get("extraction_result", result.extractions)
    normalized_summary = {
        "covered_count": len(result.covered_elements),
        "missing_count": len(result.missing_elements),
        "coverage_ratio": round(result.score / 100, 2),
        "latency_sec": result.latency_sec,
        "model_used": result.model_used,
    }
    return "\n".join(
        [
            "",
            "=== Analyze Exchange Start =====================================================",
            f"analysis_profile: {profile_id}",
            f"inference_engine_type: {_as_optional_str(trace_payload.get('inference_engine_type')) or 'unknown'}",
            f"endpoint: {_as_optional_str(trace_payload.get('endpoint')) or ''}",
            f"model: {_as_optional_str(trace_payload.get('model')) or ''}",
            f"coverage_item_prompt_length: {len(coverage_item_prompt)}",
            f"user_text_length: {len(text)}",
            "user_text_received:",
            text,
            f"llm_instruction_length: {len(llm_instruction)}",
            "llm_instruction_sent:",
            llm_instruction,
            "raw_inference_engine_response_keys:",
            _format_json(raw_response_keys),
            "raw_inference_engine_response:",
            _format_json(raw_response),
            "visualization_html:",
            _format_json(visualization_html),
            "llm_response_received:",
            _format_json(llm_response),
            "extraction_result:",
            _format_json(extraction_result),
            "normalized_analysis_summary:",
            _format_json_compact(normalized_summary),
            "=== Analyze Exchange End ===",
        ]
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: Request, payload: AnalyzeRequest) -> AnalyzeResponse:
    caller = _resolve_request_caller(request)

    try:
        context = _resolve_analysis_context(
            profile_id=payload.profile_id,
            inference_engine=payload.inference_engine,
        )
        logger.info(
            "Analyze request: caller=%s profile=%s inference_engine=%s",
            caller,
            payload.profile_id,
            context.inference_engine_key,
        )
        result = analyze_text(
            text=payload.text,
            profile_id=payload.profile_id,
            inference_engine=payload.inference_engine,
            resolved_context=context,
        )
    except ProfileNotFoundError as exc:
        logger.info(
            "Analyze request: caller=%s profile=%s inference_engine=%s",
            caller,
            payload.profile_id,
            payload.inference_engine or "unresolved",
        )
        logger.warning("Analyze rejected: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AnalysisServiceUnavailableError as exc:
        logger.warning("Analyze unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Analyze error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Erreur interne",
        ) from exc

    return AnalyzeResponse(
        score=result.score,
        decision=result.decision,
        justification=result.justification,
        profile_used=result.profile_used,
        latency_sec=result.latency_sec,
        model_used=result.model_used,
        covered_elements=result.covered_elements,
        missing_elements=result.missing_elements,
        extractions=result.extractions,
    )


def analyze_text(
    *,
    text: str,
    profile_id: str,
    inference_engine: str | None = None,
    config_dir: Path | None = None,
    inference_adapter: object = None,
    resolved_context: ResolvedAnalysisContext | None = None,
) -> AnalysisResult:
    context = resolved_context or _resolve_analysis_context(
        profile_id=profile_id,
        inference_engine=inference_engine,
        config_dir=config_dir,
    )
    profile = context.profile
    engine_key = context.inference_engine_key

    trace_logger = None
    if should_emit_prompt_trace():
        trace_logger = get_prompt_trace_logger(
            profile_name=profile_id,
            inference_engine_name=engine_key,
        )

    try:
        if hasattr(inference_adapter, "infer"):
            adapter = cast(_InferenceAdapter, inference_adapter)
            raw_result = adapter.infer(
                text=text,
                prompt=profile.prompt_text,
                criterion_ids=profile.criterion_ids,
                le_few_shot=profile.le_few_shot,
                analysis_profile_name=profile_id,
                inference_engine_key=engine_key,
            )
        else:
            raw_result = infer(
                text=text,
                prompt=profile.prompt_text,
                analysis_profile_name=profile_id,
                criterion_ids=profile.criterion_ids,
                le_few_shot=profile.le_few_shot,
                config_dir=config_dir,
                inference_engine_key=engine_key,
            )
    except InferenceClientUnavailableError as exc:
        if trace_logger is not None:
            trace_logger.info(
                "\n=== Analyze Exchange Start =====================================================\n"
                f"analysis_profile: {profile_id}\n"
                f"inference_engine: {engine_key}\n"
                f"error: {exc}\n"
                "=== Analyze Exchange End ==="
            )
        raise AnalysisServiceUnavailableError(str(exc)) from exc

    covered = _as_string_list(raw_result.get("covered_elements", []))
    missing = _as_string_list(raw_result.get("missing_elements", []))

    total_weight = sum(profile.criterion_weights.values())
    covered_weight = sum(profile.criterion_weights.get(c, 0.0) for c in covered)

    coverage_ratio = covered_weight / total_weight if total_weight > 0 else 1.0
    score = min(max(round(coverage_ratio * 100), 0), 100)

    decision: Decision = "OK"
    if score <= 30:
        decision = "KO"
    elif score <= 70 or missing:
        decision = "PARTIEL"

    justification = (
        "Completude satisfaisante."
        if decision == "OK"
        else f"Elements manquants : {', '.join(missing)}"
    )

    result = AnalysisResult(
        score=score,
        decision=decision,
        justification=justification,
        profile_used=profile_id,
        latency_sec=_as_optional_float(raw_result.get("latency_sec")),
        model_used=_as_optional_str(raw_result.get("model_used")),
        covered_elements=covered,
        missing_elements=missing,
        extractions=_as_dict_list(raw_result.get("extractions", [])),
    )

    if trace_logger is not None:
        trace_payload = raw_result.get("trace", {})
        if isinstance(trace_payload, dict):
            trace_logger.info(
                _build_trace_message(
                    profile_id=profile_id,
                    text=text,
                    trace_payload=trace_payload,
                    result=result,
                )
            )

    return result


def _resolve_analysis_context(
    *,
    profile_id: str,
    inference_engine: str | None,
    config_dir: Path | None = None,
) -> ResolvedAnalysisContext:
    profiles = load_runtime_analysis_profiles(config_dir=config_dir)
    if profile_id not in profiles:
        raise ProfileNotFoundError(f"Profil introuvable: {profile_id}")

    profile = profiles[profile_id]
    inference_engines_config = load_inference_engines_config(config_dir=config_dir)
    engine_key = (
        inference_engine
        or profile.inference_engine_key
        or inference_engines_config.default_inference_engine_key
    )
    return ResolvedAnalysisContext(profile=profile, inference_engine_key=engine_key)


def _resolve_request_caller(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "").strip()
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"

    if request.client is not None and request.client.host:
        return request.client.host

    user_agent = request.headers.get("user-agent", "").strip()
    if user_agent:
        return user_agent

    return "unknown"
