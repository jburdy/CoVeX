"""
Manage append-only case-level engine evaluation results.

Usage from the repository root:
- Imported by `tools/research/select_engines_by_cost.py` and
  `tools/research/render_engine_selection_report.py`.
- Persists JSONL rows in `artifacts/evaluation/engine_case_results.jsonl` and
  derives aggregate summaries from the latest row for each cache key.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.evaluation.evaluation_models import CaseEvaluationRecord, EngineAttempt

CASE_RESULTS_SCHEMA_VERSION = 1
SCORE_BANDS = {
    "KO": (0, 35),
    "PARTIEL": (36, 75),
    "OK": (76, 100),
}
TARGET_SCORES = {
    "KO": 15,
    "PARTIEL": 55,
    "OK": 90,
}
SUMMARY_FIELDNAMES = (
    "generated_at",
    "profile_id",
    "engine_key",
    "engine_type",
    "status",
    "qualified_threshold",
    "cost_score",
    "elapsed_total_sec",
    "avg_latency_sec",
    "band_match_rate",
    "exact_match_rate",
    "matched_count",
    "exact_match_count",
    "evaluated_count",
    "total_count",
    "error_count",
    "error",
    "first_failed_case_id",
    "expected_decision",
    "expected_score_band",
    "distance_to_target",
    "actual_score",
    "actual_decision",
    "first_evaluated_at",
    "last_evaluated_at",
)
WORST_CASE_FIELDNAMES = (
    "generated_at",
    "evaluated_at",
    "profile_id",
    "case_id",
    "engine_key",
    "engine_type",
    "cost_score",
    "expected_decision",
    "actual_decision",
    "score",
    "distance_to_target",
    "latency_sec",
    "error",
    "missing_elements",
)


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def stable_hash(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_profile_fingerprint(
    *,
    prompt_text: str,
    criterion_ids: Sequence[str],
    criterion_weights: Mapping[str, float],
    le_few_shot: Sequence[Mapping[str, object]],
) -> str:
    return stable_hash(
        {
            "prompt_text": prompt_text,
            "criterion_ids": list(criterion_ids),
            "criterion_weights": dict(sorted(criterion_weights.items())),
            "le_few_shot": list(le_few_shot),
        }
    )


def build_engine_fingerprint(
    *,
    engine_key: str,
    engine_type: str,
    model: str,
    base_url: str | None,
    timeout_sec: float | None,
) -> str:
    return stable_hash(
        {
            "engine_key": engine_key,
            "engine_type": engine_type,
            "model": model,
            "base_url": base_url,
            "timeout_sec": timeout_sec,
        }
    )


def build_params_fingerprint(params: Mapping[str, object]) -> str:
    return stable_hash(dict(params))


def build_cache_key(
    *,
    case_id: str,
    text: str,
    expected_decision: str,
    profile_fingerprint: str,
    engine_fingerprint: str,
    merged_params_fingerprint: str,
) -> str:
    return stable_hash(
        {
            "schema_version": CASE_RESULTS_SCHEMA_VERSION,
            "case_id": case_id,
            "text": text,
            "expected_decision": expected_decision,
            "profile_fingerprint": profile_fingerprint,
            "engine_fingerprint": engine_fingerprint,
            "merged_params_fingerprint": merged_params_fingerprint,
        }
    )


def decision_to_band(decision: str) -> tuple[int, int]:
    return SCORE_BANDS[decision]


def format_band(decision: str) -> str:
    lower, upper = decision_to_band(decision)
    return f"{lower}-{upper}"


def score_matches_expected(*, expected_decision: str, actual_score: int) -> bool:
    lower, upper = decision_to_band(expected_decision)
    return lower <= actual_score <= upper


def distance_to_target(*, expected_decision: str, actual_score: int) -> int:
    return abs(actual_score - TARGET_SCORES[expected_decision])


def load_case_results(path: Path) -> dict[str, CaseEvaluationRecord]:
    if not path.exists():
        return {}

    results: dict[str, CaseEvaluationRecord] = {}
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            record = _parse_case_record(payload)
            results[record.cache_key] = record
    return results


def append_case_result(path: Path, record: CaseEvaluationRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_record_to_payload(record), ensure_ascii=False) + "\n")


def summarize_engine_attempt(
    *,
    generated_at: str,
    profile_id: str,
    engine_key: str,
    engine_type: str,
    cost_score: int | None,
    case_records: Sequence[CaseEvaluationRecord | None],
    threshold: float,
) -> EngineAttempt:
    evaluated_records = [record for record in case_records if record is not None]
    total_count = len(case_records)
    evaluated_count = len(evaluated_records)
    matched_count = sum(1 for record in evaluated_records if record.band_match)
    exact_match_count = sum(1 for record in evaluated_records if record.exact_match)
    error_count = sum(1 for record in evaluated_records if record.error is not None)
    latency_values = [
        record.latency_sec
        for record in evaluated_records
        if record.latency_sec is not None
    ]
    elapsed_total_sec = sum(latency_values) if latency_values else None
    avg_latency_sec = (
        sum(latency_values) / len(latency_values) if latency_values else None
    )
    band_match_rate = 0.0 if total_count == 0 else matched_count / total_count
    complete = evaluated_count == total_count
    qualified_threshold = complete and error_count == 0 and band_match_rate >= threshold

    first_failed = next(
        (record for record in case_records if record is not None and record.failed),
        None,
    )
    timestamps = [record.evaluated_at for record in evaluated_records]

    return EngineAttempt(
        engine_key=engine_key,
        cost_score=cost_score,
        elapsed_sec=elapsed_total_sec,
        matched_count=matched_count,
        total_count=total_count,
        profile_id=profile_id,
        engine_type=engine_type,
        error=None if first_failed is None else first_failed.error,
        mismatch_entry_id=None if first_failed is None else first_failed.case_id,
        mismatch_expected=None
        if first_failed is None
        else first_failed.expected_decision,
        mismatch_expected_band=(
            None
            if first_failed is None
            else format_band(first_failed.expected_decision)
        ),
        mismatch_distance_to_target=(
            None if first_failed is None else first_failed.distance_to_target
        ),
        mismatch_actual_score=None if first_failed is None else first_failed.score,
        mismatch_actual=None if first_failed is None else first_failed.actual_decision,
        band_match_rate=band_match_rate,
        avg_latency_sec=avg_latency_sec,
        error_count=error_count,
        exact_match_count=exact_match_count,
        evaluated_count=evaluated_count,
        generated_at=generated_at,
        first_evaluated_at=min(timestamps) if timestamps else None,
        last_evaluated_at=max(timestamps) if timestamps else None,
        qualified_threshold=qualified_threshold,
    )


def select_recommended_attempt(
    *,
    engine_keys: Sequence[str],
    attempts_by_engine: Mapping[str, EngineAttempt],
) -> EngineAttempt | None:
    for engine_key in engine_keys:
        attempt = attempts_by_engine.get(engine_key)
        if attempt is not None and attempt.qualified_threshold:
            return attempt
    return None


def build_worst_case_rows(
    *,
    generated_at: str,
    case_results: Iterable[CaseEvaluationRecord],
) -> list[dict[str, str]]:
    failed_records = [record for record in case_results if record.failed]
    failed_records.sort(key=_worst_case_sort_key)
    rows: list[dict[str, str]] = []
    for record in failed_records:
        rows.append(
            {
                "generated_at": generated_at,
                "evaluated_at": record.evaluated_at,
                "profile_id": record.profile_id,
                "case_id": record.case_id,
                "engine_key": record.engine_key,
                "engine_type": record.engine_type,
                "cost_score": _format_optional_int(record.cost_score),
                "expected_decision": record.expected_decision,
                "actual_decision": record.actual_decision or "",
                "score": _format_optional_int(record.score),
                "distance_to_target": _format_optional_int(record.distance_to_target),
                "latency_sec": _format_optional_float(record.latency_sec),
                "error": record.error or "",
                "missing_elements": ", ".join(record.missing_elements),
            }
        )
    return rows


def _worst_case_sort_key(
    record: CaseEvaluationRecord,
) -> tuple[int, int, float, str, str]:
    error_rank = 0 if record.error is not None else 1
    distance = -(record.distance_to_target or 0)
    latency = -(record.latency_sec or 0.0)
    return (error_rank, distance, latency, record.profile_id, record.case_id)


def _parse_case_record(payload: Mapping[str, object]) -> CaseEvaluationRecord:
    return CaseEvaluationRecord(
        cache_key=str(payload["cache_key"]),
        evaluated_at=str(payload["evaluated_at"]),
        case_id=str(payload["case_id"]),
        profile_id=str(payload["profile_id"]),
        text_hash=str(payload["text_hash"]),
        expected_decision=str(payload["expected_decision"]),
        profile_fingerprint=str(payload["profile_fingerprint"]),
        engine_fingerprint=str(payload["engine_fingerprint"]),
        merged_params_fingerprint=str(payload["merged_params_fingerprint"]),
        engine_key=str(payload["engine_key"]),
        engine_type=str(payload["engine_type"]),
        cost_score=_coerce_optional_int(payload.get("cost_score")),
        model_used=_coerce_optional_str(payload.get("model_used")),
        actual_decision=_coerce_optional_str(payload.get("actual_decision")),
        score=_coerce_optional_int(payload.get("score")),
        band_match=bool(payload.get("band_match", False)),
        exact_match=bool(payload.get("exact_match", False)),
        distance_to_target=_coerce_optional_int(payload.get("distance_to_target")),
        latency_sec=_coerce_optional_float(payload.get("latency_sec")),
        error=_coerce_optional_str(payload.get("error")),
        covered_elements=tuple(_coerce_str_list(payload.get("covered_elements"))),
        missing_elements=tuple(_coerce_str_list(payload.get("missing_elements"))),
    )


def _record_to_payload(record: CaseEvaluationRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload["schema_version"] = CASE_RESULTS_SCHEMA_VERSION
    payload["covered_elements"] = list(record.covered_elements)
    payload["missing_elements"] = list(record.missing_elements)
    return payload


def _coerce_optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return int(str(value))


def _coerce_optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value))


def _coerce_optional_str(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _coerce_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _format_optional_int(value: int | None) -> str:
    return "" if value is None else str(value)


def _format_optional_float(value: float | None) -> str:
    return "" if value is None else f"{value:.3f}"
