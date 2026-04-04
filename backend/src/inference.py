"""
Charge la configuration des moteurs et execute les appels d'inference LLM.

Usage:
- Module importe par `backend/src/analysis.py` pour resoudre un moteur et lancer une inference.
- Reutilise par `tools/research/select_engines_by_cost_score.py` pour evaluer les moteurs hors API.
"""

from __future__ import annotations

from datetime import datetime
import logging
import os
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, Mapping, cast

import langextract as lx
import yaml
from langextract.core.format_handler import FormatHandler
from langextract.providers.ollama import OllamaLanguageModel
from langextract.providers.openai import OpenAILanguageModel
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

CONFIG_DIRECTORY = "config"
INFERENCE_ENGINES_FILE = "inference_engines.yaml"
DEFAULT_LOCAL_URL = "http://127.0.0.1:11434"
DEFAULT_INFERENCE_TIMEOUT_SEC = 30.0
LANGEXTRACT_HTML_DIRECTORY = Path("artifacts") / "langextract_html"
ENV_VAR_ALIASES: dict[str, tuple[str, ...]] = {
    "GOOGLE_API_KEY": ("COVEX_GOOGLE_API_KEY",),
    "COVEX_GOOGLE_API_KEY": ("GOOGLE_API_KEY",),
}


class BrainEnginesConfigurationError(RuntimeError):
    pass


class InferenceClientUnavailableError(RuntimeError):
    pass


class CoVeXOllamaLanguageModel(OllamaLanguageModel):
    def _ollama_query(self, *args: Any, **kwargs: Any) -> Mapping[str, Any]:
        response = super()._ollama_query(*args, **kwargs)
        raw_response = response.get("response")
        thinking_response = response.get("thinking")

        if isinstance(raw_response, str) and raw_response.strip():
            return response

        if isinstance(thinking_response, str) and thinking_response.strip():
            patched_response = dict(response)
            patched_response["response"] = thinking_response
            return patched_response

        return response


class BrainEngineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["local", "remote"]
    model: str = Field(min_length=1)
    justification: str | None = Field(default=None, min_length=1)
    cost_score: int | None = Field(default=None, ge=1)
    base_url: str | None = None
    auth_env_var: str | None = None
    timeout_sec: float | None = Field(default=None, gt=0)


class BrainEnginesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    default_inference_engine: str = Field(min_length=1)
    inference_engines: dict[str, BrainEngineConfig]

    @property
    def default_inference_engine_key(self) -> str:
        return self.default_inference_engine


_cached_config: BrainEnginesConfig | None = None


def load_inference_engines_config(*, config_dir: Path | None = None) -> BrainEnginesConfig:
    global _cached_config
    if _cached_config is not None and config_dir is None:
        return _cached_config

    resolved_dir = config_dir or _resolve_default_config_dir()
    path = resolved_dir / INFERENCE_ENGINES_FILE
    if not path.exists():
        raise BrainEnginesConfigurationError(f"Missing required configuration file: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            payload = yaml.safe_load(file)
        config = BrainEnginesConfig.model_validate(payload)
        if config_dir is None:
            _cached_config = config
        return config
    except Exception as exc:
        raise BrainEnginesConfigurationError(f"Invalid brain engines config: {exc}") from exc


def resolve_inference_engine(
    inference_engines_config: BrainEnginesConfig, *, inference_engine_key: str | None = None
) -> tuple[str, BrainEngineConfig]:
    key = inference_engine_key or inference_engines_config.default_inference_engine_key
    engine = inference_engines_config.inference_engines.get(key)
    if engine is None:
        raise BrainEnginesConfigurationError(f"Brain engine not found: {key}")
    return key, engine


def infer(
    text: str,
    prompt: str,
    timeout_sec: float | None = None,
    *,
    analysis_profile_name: str | None = None,
    criterion_ids: list[str] | None = None,
    le_few_shot: list[dict[str, object]] | None = None,
    config_dir: Path | None = None,
    inference_engine_key: str | None = None,
) -> dict[str, object]:
    from settings import ensure_project_env_loaded

    ensure_project_env_loaded()

    config = load_inference_engines_config(config_dir=config_dir)
    key, engine = resolve_inference_engine(config, inference_engine_key=inference_engine_key)

    resolved_timeout = _resolve_timeout_sec(engine, timeout_sec)
    resolved_criterion_ids = list(criterion_ids or [])

    examples = _build_examples(le_few_shot)

    model = _build_langextract_model(engine, resolved_timeout)
    llm_instruction = _render_llm_instruction(
        prompt=prompt, text=text, examples=examples, model=model
    )

    started_at = perf_counter()
    try:
        extraction_result = lx.extract(
            text_or_documents=text,
            prompt_description=prompt,
            examples=examples,
            model=model,
            use_schema_constraints=False,
            prompt_validation_level=lx.prompt_validation.PromptValidationLevel.OFF,
        )
    except Exception as exc:
        raise InferenceClientUnavailableError(_describe_inference_failure(engine, exc)) from exc
    elapsed = perf_counter() - started_at

    if isinstance(extraction_result, lx.data.AnnotatedDocument):
        doc: lx.data.AnnotatedDocument = extraction_result
    else:
        documents = cast(list[lx.data.AnnotatedDocument], extraction_result)
        doc = documents[0]
    visualization_html_path = _save_visualization_html(
        doc=doc,
        analysis_profile_name=analysis_profile_name,
        inference_engine_key=key,
    )
    doc_extractions = list(doc.extractions) if doc.extractions else []
    covered = list(
        set(
            (ext.attributes or {}).get("criterion_id")
            or ext.extraction_class
            or ext.extraction_text
            for ext in doc_extractions
        )
    )
    missing = [c for c in resolved_criterion_ids if c not in covered]
    ratio = len(covered) / len(resolved_criterion_ids) if resolved_criterion_ids else 1.0

    extractions = [
        {
            "class": getattr(ext, "extraction_class", None),
            "text": getattr(ext, "extraction_text", None),
            "criterion_id": (ext.attributes or {}).get("criterion_id"),
        }
        for ext in doc_extractions
    ]

    return {
        "covered_elements": covered,
        "missing_elements": missing,
        "coverage_ratio": ratio,
        "model_used": engine.model,
        "latency_sec": elapsed,
        "extractions": extractions,
        "trace": {
            "inference_engine_type": engine.type,
            "endpoint": _resolve_engine_endpoint(engine),
            "model": engine.model,
            "coverage_item_prompt": prompt,
            "llm_instruction_sent": llm_instruction,
            "raw_inference_engine_response_keys": [],
            "raw_inference_engine_response": {
                "available": False,
                "reason": "Provider raw response is not exposed by the current langextract integration.",
            },
            "visualization_html": {
                "available": visualization_html_path is not None,
                "path": str(visualization_html_path) if visualization_html_path else None,
            },
            "llm_response_received": {
                "covered_elements": covered,
                "missing_elements": missing,
                "coverage_ratio": ratio,
            },
            "extraction_result": extractions,
        },
    }


def _build_examples(
    le_few_shot: list[dict[str, object]] | None,
) -> list[lx.data.ExampleData]:
    examples = []
    for ex in le_few_shot or []:
        raw_extractions = ex.get("extractions", [])
        extraction_items = raw_extractions if isinstance(raw_extractions, list) else []
        extractions = [
            lx.data.Extraction(
                extraction_class="covered_criterion",
                extraction_text=str(ext.get("extraction_text", "")),
                attributes={"criterion_id": str(ext.get("criterion_id", ""))},
            )
            for ext in extraction_items
            if isinstance(ext, dict)
        ]
        examples.append(lx.data.ExampleData(text=str(ex.get("text", "")), extractions=extractions))
    return examples


def _save_visualization_html(
    *,
    doc: lx.data.AnnotatedDocument,
    analysis_profile_name: str | None,
    inference_engine_key: str,
) -> Path | None:
    try:
        html_content = lx.visualize(doc)
        rendered_html = _extract_visualization_html_content(html_content)
    except Exception:
        logger.warning("Unable to render LangExtract visualization HTML", exc_info=True)
        return None

    output_dir = _project_root() / LANGEXTRACT_HTML_DIRECTORY
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    profile_slug = _slugify_path_component(analysis_profile_name or "inline-prompt")
    engine_slug = _slugify_path_component(inference_engine_key)
    output_path = output_dir / f"langextract-{timestamp}-{engine_slug}-{profile_slug}.html"

    try:
        output_path.write_text(rendered_html, encoding="utf-8")
    except OSError:
        logger.warning("Unable to save LangExtract visualization HTML", exc_info=True)
        return None

    logger.info("Saved LangExtract visualization to %s", output_path)
    return output_path


def _extract_visualization_html_content(html_content: object) -> str:
    if isinstance(html_content, str):
        return html_content

    rendered_html = getattr(html_content, "data", None)
    if isinstance(rendered_html, str):
        return rendered_html

    raise TypeError("Unsupported LangExtract visualization payload type")


def _render_llm_instruction(
    *, prompt: str, text: str, examples: list[lx.data.ExampleData], model: object
) -> str:
    format_handler = FormatHandler(
        format_type=lx.data.FormatType.JSON,
        use_wrapper=True,
        wrapper_key=lx.data.EXTRACTIONS_KEY,
        use_fences=getattr(model, "requires_fence_output", False),
        attribute_suffix=lx.data.ATTRIBUTE_SUFFIX,
    )
    template = lx.prompting.PromptTemplateStructured(description=prompt, examples=examples)
    generator = lx.prompting.QAPromptGenerator(
        template=template,
        format_handler=format_handler,
    )
    return generator.render(question=text)


def _resolve_engine_endpoint(inference_engine: BrainEngineConfig) -> str:
    if inference_engine.base_url:
        return _normalize_openai_base_url(inference_engine.base_url)
    if inference_engine.type == "local":
        return DEFAULT_LOCAL_URL
    return ""


def _resolve_timeout_sec(
    inference_engine: BrainEngineConfig,
    requested_timeout_sec: float | None,
) -> float:
    if inference_engine.timeout_sec is not None:
        return inference_engine.timeout_sec
    if requested_timeout_sec is not None:
        return requested_timeout_sec
    return DEFAULT_INFERENCE_TIMEOUT_SEC


def _describe_inference_failure(
    inference_engine: BrainEngineConfig,
    exc: Exception,
) -> str:
    messages = []
    current: BaseException | None = exc
    while current is not None:
        message = str(current).strip()
        if message and message not in messages:
            messages.append(message)
        current = current.__cause__

    joined_messages = " | ".join(messages)
    lowered_messages = joined_messages.lower()
    engine_label = f"{inference_engine.type}:{inference_engine.model}"

    if "can't find ollama" in lowered_messages:
        return f"Moteur {engine_label} introuvable dans Ollama. Lancez `ollama run {inference_engine.model}`."

    if "timed out" in lowered_messages or "timeout" in lowered_messages:
        timeout_sec = _resolve_timeout_sec(inference_engine, None)
        return (
            f"Moteur {engine_label} indisponible: delai depasse apres {int(round(timeout_sec))} s. "
            f"Detail: {joined_messages}"
        )

    if joined_messages:
        return f"Moteur {engine_label} indisponible. Detail: {joined_messages}"

    return f"Moteur {engine_label} indisponible."


def _build_langextract_model(
    inference_engine: BrainEngineConfig,
    timeout_sec: float,
) -> object:
    timeout_value = max(1, int(round(timeout_sec)))

    if inference_engine.type == "remote":
        credential = _resolve_engine_credential(inference_engine)
        return OpenAILanguageModel(
            model_id=inference_engine.model,
            api_key=credential or "dummy",
            base_url=_resolve_engine_endpoint(inference_engine),
            temperature=0.0,
            timeout=timeout_value,
        )

    return CoVeXOllamaLanguageModel(
        model_id=inference_engine.model,
        base_url=inference_engine.base_url or DEFAULT_LOCAL_URL,
        timeout=timeout_value,
        temperature=0.0,
    )


def _resolve_engine_credential(inference_engine: BrainEngineConfig) -> str | None:
    candidate_names: list[str] = []
    if inference_engine.auth_env_var:
        candidate_names.append(inference_engine.auth_env_var)
        candidate_names.extend(ENV_VAR_ALIASES.get(inference_engine.auth_env_var, ()))

    for name in candidate_names:
        credential = os.getenv(name)
        if credential:
            return credential

    return None


def _normalize_openai_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized == "https://openrouter.ai":
        return f"{normalized}/api/v1"
    return normalized


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _slugify_path_component(value: str) -> str:
    slug = "".join(
        character if character.isalnum() or character in {"-", "_"} else "-"
        for character in value.strip().lower()
    )
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or "unknown"


def _resolve_default_config_dir() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / CONFIG_DIRECTORY
        if candidate.exists() and candidate.is_dir():
            return candidate
    return Path(CONFIG_DIRECTORY)
