"""
Modeles et coercions partages pour les artefacts d'evaluation des moteurs.

Usage:
- Module importe par `tools/research/select_engines_by_cost.py` et
  `tools/research/render_engine_selection_report.py`.
- Defini les lignes case-level persistees en JSONL et les syntheses CSV.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CaseEvaluationRecord:
    cache_key: str
    evaluated_at: str
    case_id: str
    profile_id: str
    text_hash: str
    expected_decision: str
    profile_fingerprint: str
    engine_fingerprint: str
    merged_params_fingerprint: str
    engine_key: str
    engine_type: str
    cost_score: int | None
    model_used: str | None
    actual_decision: str | None
    score: int | None
    band_match: bool
    exact_match: bool
    distance_to_target: int | None
    latency_sec: float | None
    error: str | None
    covered_elements: tuple[str, ...] = ()
    missing_elements: tuple[str, ...] = ()

    @property
    def failed(self) -> bool:
        return self.error is not None or not self.band_match


@dataclass(frozen=True)
class EngineAttempt:
    engine_key: str
    cost_score: int | None
    elapsed_sec: float | None
    matched_count: int
    total_count: int
    profile_id: str = ""
    engine_type: str | None = None
    error: str | None = None
    mismatch_entry_id: str | None = None
    mismatch_expected: str | None = None
    mismatch_expected_band: str | None = None
    mismatch_distance_to_target: int | None = None
    mismatch_actual_score: int | None = None
    mismatch_actual: str | None = None
    band_match_rate: float | None = None
    avg_latency_sec: float | None = None
    error_count: int = 0
    exact_match_count: int = 0
    evaluated_count: int = 0
    generated_at: str | None = None
    first_evaluated_at: str | None = None
    last_evaluated_at: str | None = None
    qualified_threshold: bool = False

    @property
    def success(self) -> bool:
        return (
            self.complete
            and self.error_count == 0
            and self.error is None
            and self.matched_count == self.total_count
        )

    @property
    def complete(self) -> bool:
        return self.evaluated_count == self.total_count

    @property
    def status(self) -> str:
        return self.status_label

    @property
    def ratio(self) -> float:
        if self.band_match_rate is not None:
            return self.band_match_rate
        return 0.0 if self.total_count == 0 else self.matched_count / self.total_count

    @property
    def distance(self) -> int:
        if self.success:
            return 0
        if self.mismatch_distance_to_target is not None:
            return self.mismatch_distance_to_target
        return 10**9

    @property
    def status_label(self) -> str:
        if self.success:
            return "PASS"
        if self.qualified_threshold:
            return "QUALIFIED"
        if not self.complete:
            return "INCOMPLETE"
        if self.error:
            return "ERROR"
        return "FAILED"


def coerce_optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        if not value.strip():
            return None
        return int(value)
    raise ValueError(f"Valeur entiere invalide: {value!r}")


def coerce_optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError(f"Valeur flottante invalide: {value!r}")


def coerce_optional_str(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def coerce_optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return None
        if normalized in {"1", "true", "yes", "y"}:
            return True
        if normalized in {"0", "false", "no", "n"}:
            return False
    raise ValueError(f"Valeur booleenne invalide: {value!r}")
