"""Verifie le cache et les syntheses de selection des moteurs."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.evaluation.engine_case_store import (  # noqa: E402
    append_case_result,
    build_cache_key,
    build_engine_fingerprint,
    build_params_fingerprint,
    build_profile_fingerprint,
    build_worst_case_rows,
    load_case_results,
    select_recommended_attempt,
    summarize_engine_attempt,
)
from tools.evaluation.evaluation_models import (  # noqa: E402
    CaseEvaluationRecord,
    EngineAttempt,
)
from tools.research.select_engines_by_cost import is_systemic_engine_error  # noqa: E402


def test_build_cache_key_changes_when_profile_or_engine_changes() -> None:
    params_fingerprint = build_params_fingerprint({})
    profile_fingerprint_a = build_profile_fingerprint(
        prompt_text="Prompt A",
        criterion_ids=["critere_a"],
        criterion_weights={"critere_a": 1.0},
        le_few_shot=[],
    )
    profile_fingerprint_b = build_profile_fingerprint(
        prompt_text="Prompt B",
        criterion_ids=["critere_a"],
        criterion_weights={"critere_a": 1.0},
        le_few_shot=[],
    )
    engine_fingerprint_a = build_engine_fingerprint(
        engine_key="engine_a",
        engine_type="remote",
        model="model-a",
        base_url="https://example.test",
        timeout_sec=30.0,
    )
    engine_fingerprint_b = build_engine_fingerprint(
        engine_key="engine_a",
        engine_type="remote",
        model="model-b",
        base_url="https://example.test",
        timeout_sec=30.0,
    )

    cache_key_a = build_cache_key(
        case_id="CASE-1",
        text="Bonjour",
        expected_decision="OK",
        profile_fingerprint=profile_fingerprint_a,
        engine_fingerprint=engine_fingerprint_a,
        merged_params_fingerprint=params_fingerprint,
    )
    cache_key_b = build_cache_key(
        case_id="CASE-1",
        text="Bonjour",
        expected_decision="OK",
        profile_fingerprint=profile_fingerprint_b,
        engine_fingerprint=engine_fingerprint_a,
        merged_params_fingerprint=params_fingerprint,
    )
    cache_key_c = build_cache_key(
        case_id="CASE-1",
        text="Bonjour",
        expected_decision="OK",
        profile_fingerprint=profile_fingerprint_a,
        engine_fingerprint=engine_fingerprint_b,
        merged_params_fingerprint=params_fingerprint,
    )

    assert cache_key_a != cache_key_b
    assert cache_key_a != cache_key_c


def test_load_case_results_keeps_latest_row_for_same_cache_key(tmp_path: Path) -> None:
    results_path = tmp_path / "engine_case_results.jsonl"
    append_case_result(
        results_path,
        _make_record(cache_key="shared", evaluated_at="2026-03-14T10:00:00Z", score=20),
    )
    append_case_result(
        results_path,
        _make_record(cache_key="shared", evaluated_at="2026-03-14T10:05:00Z", score=90),
    )

    loaded = load_case_results(results_path)

    assert loaded["shared"].score == 90
    assert loaded["shared"].evaluated_at == "2026-03-14T10:05:00Z"


def test_summarize_engine_attempt_qualifies_at_80_percent_only_when_complete() -> None:
    records = [
        _make_record(case_id="CASE-1", score=10, band_match=True, exact_match=True),
        _make_record(case_id="CASE-2", score=55, band_match=True, exact_match=True),
        _make_record(case_id="CASE-3", score=90, band_match=True, exact_match=True),
        _make_record(case_id="CASE-4", score=45, band_match=True, exact_match=False),
        _make_record(
            case_id="CASE-5",
            expected_decision="PARTIEL",
            actual_decision="OK",
            score=90,
            band_match=False,
            exact_match=False,
            distance_to_target=35,
        ),
    ]

    qualified_summary = summarize_engine_attempt(
        generated_at="2026-03-14T10:00:00Z",
        profile_id="profil_demo",
        engine_key="cheap_engine",
        engine_type="remote",
        cost_score=2,
        case_records=records,
        threshold=0.9,
    )
    incomplete_summary = summarize_engine_attempt(
        generated_at="2026-03-14T10:00:00Z",
        profile_id="profil_demo",
        engine_key="cheap_engine",
        engine_type="remote",
        cost_score=2,
        case_records=[records[0], records[1], records[2], records[3], None],
        threshold=0.9,
    )

    assert qualified_summary.qualified_threshold is False
    assert qualified_summary.success is False
    assert qualified_summary.status_label == "FAILED"
    assert qualified_summary.mismatch_entry_id == "CASE-5"
    assert qualified_summary.matched_count == 4
    assert qualified_summary.total_count == 5

    assert incomplete_summary.qualified_threshold is False
    assert incomplete_summary.status_label == "INCOMPLETE"
    assert incomplete_summary.ratio == 0.8
    assert incomplete_summary.evaluated_count == 4


def test_summarize_engine_attempt_does_not_qualify_when_a_technical_error_exists() -> None:
    records = [
        _make_record(case_id="CASE-1", expected_decision="KO", actual_decision="KO", score=15),
        _make_record(
            case_id="CASE-2", expected_decision="PARTIEL", actual_decision="PARTIEL", score=55
        ),
        _make_record(case_id="CASE-3", expected_decision="OK", actual_decision="OK", score=90),
        _make_record(case_id="CASE-4", expected_decision="KO", actual_decision="KO", score=10),
        _make_record(
            case_id="CASE-5",
            expected_decision="KO",
            actual_decision=None,
            score=None,
            band_match=False,
            exact_match=False,
            distance_to_target=None,
            error="Provider timeout",
        ),
    ]

    summary = summarize_engine_attempt(
        generated_at="2026-03-14T10:00:00Z",
        profile_id="profil_demo",
        engine_key="cheap_engine",
        engine_type="remote",
        cost_score=2,
        case_records=records,
        threshold=0.9,
    )

    assert summary.ratio == 0.8
    assert summary.error_count == 1
    assert summary.qualified_threshold is False
    assert summary.status_label == "ERROR"


def test_select_recommended_attempt_prefers_cheapest_qualified_engine() -> None:
    cheap_attempt = EngineAttempt(
        engine_key="cheap_engine",
        cost_score=2,
        elapsed_sec=12.0,
        matched_count=4,
        total_count=5,
        profile_id="profil_demo",
        band_match_rate=0.9,
        avg_latency_sec=2.4,
        evaluated_count=5,
        qualified_threshold=True,
    )
    premium_attempt = EngineAttempt(
        engine_key="premium_engine",
        cost_score=10,
        elapsed_sec=8.0,
        matched_count=5,
        total_count=5,
        profile_id="profil_demo",
        band_match_rate=1.0,
        avg_latency_sec=1.6,
        evaluated_count=5,
        qualified_threshold=True,
    )

    recommended = select_recommended_attempt(
        engine_keys=["cheap_engine", "premium_engine"],
        attempts_by_engine={
            "cheap_engine": cheap_attempt,
            "premium_engine": premium_attempt,
        },
    )

    assert recommended is not None
    assert recommended.engine_key == "cheap_engine"


def test_build_worst_case_rows_orders_errors_before_band_misses() -> None:
    rows = build_worst_case_rows(
        generated_at="2026-03-14T10:00:00Z",
        case_results=[
            _make_record(
                case_id="CASE-BAND",
                expected_decision="PARTIEL",
                actual_decision="OK",
                score=90,
                band_match=False,
                exact_match=False,
                distance_to_target=35,
                missing_elements=("critere_manquant",),
            ),
            _make_record(
                case_id="CASE-ERR",
                expected_decision="OK",
                actual_decision=None,
                score=None,
                band_match=False,
                exact_match=False,
                distance_to_target=None,
                error="Timeout provider",
            ),
        ],
    )

    assert rows[0]["case_id"] == "CASE-ERR"
    assert rows[1]["case_id"] == "CASE-BAND"
    assert rows[1]["missing_elements"] == "critere_manquant"


def test_is_systemic_engine_error_detects_provider_configuration_failures() -> None:
    assert is_systemic_engine_error("API key not valid. Please pass a valid API key.")
    assert is_systemic_engine_error("OpenAI API error: 'str' object has no attribute 'choices'")
    assert not is_systemic_engine_error("Content must contain an 'extractions' key.")


def _make_record(
    *,
    cache_key: str = "cache-key",
    evaluated_at: str = "2026-03-14T10:00:00Z",
    case_id: str = "CASE-1",
    profile_id: str = "profil_demo",
    expected_decision: str = "OK",
    actual_decision: str | None = "OK",
    score: int | None = 90,
    band_match: bool = True,
    exact_match: bool = True,
    distance_to_target: int | None = 0,
    error: str | None = None,
    missing_elements: tuple[str, ...] = (),
) -> CaseEvaluationRecord:
    return CaseEvaluationRecord(
        cache_key=cache_key,
        evaluated_at=evaluated_at,
        case_id=case_id,
        profile_id=profile_id,
        text_hash="text-hash",
        expected_decision=expected_decision,
        profile_fingerprint="profile-fingerprint",
        engine_fingerprint="engine-fingerprint",
        merged_params_fingerprint="params-fingerprint",
        engine_key="engine-demo",
        engine_type="remote",
        cost_score=3,
        model_used="model-demo",
        actual_decision=actual_decision,
        score=score,
        band_match=band_match,
        exact_match=exact_match,
        distance_to_target=distance_to_target,
        latency_sec=1.25,
        error=error,
        covered_elements=("critere_ok",),
        missing_elements=missing_elements,
    )
