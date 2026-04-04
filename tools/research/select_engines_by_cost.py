"""
Benchmark candidate engines against the golden dataset with case-level caching.

Execution from the repository root:
- `uv run --project backend python tools/research/select_engines_by_cost.py`
- `uv run --project backend python tools/research/select_engines_by_cost.py --refresh`
- Updates `artifacts/evaluation/engine_case_results.jsonl`,
  `artifacts/evaluation/engine_selection_results.csv`,
  `artifacts/evaluation/engine_worst_cases.csv`, and
  `artifacts/evaluation/engine_selection_report.md`.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, cast

SCRIPT_PATH = Path(__file__).resolve()
ROOT_DIR = SCRIPT_PATH.parents[2]
BACKEND_SRC_DIR = ROOT_DIR / "backend" / "src"
ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "evaluation"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC_DIR))

from tools.evaluation.engine_case_store import (  # noqa: E402
    SUMMARY_FIELDNAMES,
    WORST_CASE_FIELDNAMES,
    append_case_result,
    build_cache_key,
    build_engine_fingerprint,
    build_params_fingerprint,
    build_profile_fingerprint,
    build_worst_case_rows,
    distance_to_target,
    hash_text,
    load_case_results,
    score_matches_expected,
    select_recommended_attempt,
    summarize_engine_attempt,
    utc_now_iso,
)
from tools.evaluation.evaluation_models import CaseEvaluationRecord, EngineAttempt  # noqa: E402

DATASET_PATH = ROOT_DIR / "datasets" / "golden_dataset.jsonl"
CONFIG_DIR = ROOT_DIR / "config"
ENGINES_PATH = SCRIPT_PATH.with_name("engine_candidates.txt")
CASE_RESULTS_PATH = ARTIFACTS_DIR / "engine_case_results.jsonl"
RESULTS_PATH = ARTIFACTS_DIR / "engine_selection_results.csv"
WORST_CASES_PATH = ARTIFACTS_DIR / "engine_worst_cases.csv"
REPORT_PATH = ARTIFACTS_DIR / "engine_selection_report.md"
TIMEOUT_SEC = 30.0
DEFAULT_THRESHOLD = 0.9
DEFAULT_REMOTE_WORKERS = 4
VALID_DECISIONS = {"KO", "PARTIEL", "OK"}
SYSTEMIC_ENGINE_ERROR_MARKERS = (
    "api key not valid",
    "api_key_invalid",
    "attribute 'choices'",
    "can't find ollama",
    "connection refused",
    "unauthorized",
    "forbidden",
    "authentication",
)


def _load_backend_helpers() -> tuple[Any, Any, Any, Any]:
    from analysis import analyze_text  # type: ignore[import-not-found]
    from analysis_profiles_config import (  # type: ignore[import-not-found]
        load_runtime_analysis_profiles,
    )
    from inference import infer, load_inference_engines_config  # type: ignore[import-not-found]

    return (
        analyze_text,
        load_runtime_analysis_profiles,
        load_inference_engines_config,
        infer,
    )


(
    _ANALYZE_TEXT,
    _LOAD_RUNTIME_ANALYSIS_PROFILES,
    _LOAD_INFERENCE_ENGINES_CONFIG,
    _BACKEND_INFER,
) = _load_backend_helpers()
ANALYZE_TEXT = cast(Callable[..., Any], _ANALYZE_TEXT)
LOAD_RUNTIME_ANALYSIS_PROFILES = cast(
    Callable[..., Any], _LOAD_RUNTIME_ANALYSIS_PROFILES
)
LOAD_INFERENCE_ENGINES_CONFIG = cast(Callable[..., Any], _LOAD_INFERENCE_ENGINES_CONFIG)
BACKEND_INFER = cast(Callable[..., Any], _BACKEND_INFER)


@dataclass(frozen=True)
class DatasetEntry:
    id: str
    profile_id: str
    text: str
    decision_expected: str


@dataclass(frozen=True)
class DirectInferenceAdapter:
    config_dir: Path
    timeout_sec: float

    def infer(self, **kwargs: object) -> dict[str, object]:
        return cast(
            dict[str, object],
            BACKEND_INFER(
                text=str(kwargs.get("text", "")),
                prompt=str(kwargs.get("prompt", "")),
                timeout_sec=self.timeout_sec,
                criterion_ids=cast(list[str] | None, kwargs.get("criterion_ids")),
                le_few_shot=cast(
                    list[dict[str, object]] | None,
                    kwargs.get("le_few_shot"),
                ),
                config_dir=self.config_dir,
                inference_engine_key=cast(
                    str | None,
                    kwargs.get("inference_engine_key"),
                ),
            ),
        )


@dataclass(frozen=True)
class CaseEvaluationContext:
    entry: DatasetEntry
    cache_key: str
    profile_fingerprint: str
    engine_fingerprint: str
    merged_params_fingerprint: str
    engine_key: str
    engine_type: str
    cost_score: int | None


def load_dataset_entries(path: Path) -> list[DatasetEntry]:
    entries: list[DatasetEntry] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped_line = raw_line.strip()
            if not stripped_line:
                continue
            payload = json.loads(stripped_line)
            if not isinstance(payload, dict):
                raise ValueError(f"Ligne {line_number} invalide dans {path}")

            decision_expected = read_required_string(
                payload,
                key="decision_expected",
                line_number=line_number,
                path=path,
            ).upper()
            if decision_expected not in VALID_DECISIONS:
                raise ValueError(
                    f"decision_expected invalide a la ligne {line_number} dans {path}: "
                    f"{decision_expected}"
                )

            entries.append(
                DatasetEntry(
                    id=read_required_string(
                        payload,
                        key="id",
                        line_number=line_number,
                        path=path,
                    ),
                    profile_id=read_required_string(
                        payload,
                        key="profile_id",
                        line_number=line_number,
                        path=path,
                    ),
                    text=read_required_string(
                        payload,
                        key="text",
                        line_number=line_number,
                        path=path,
                    ),
                    decision_expected=decision_expected,
                )
            )
    return entries


def read_required_string(
    payload: dict[str, object],
    *,
    key: str,
    line_number: int,
    path: Path,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Champ {key!r} invalide a la ligne {line_number} dans {path}")
    return value.strip()


def group_entries_by_profile(
    entries: list[DatasetEntry],
) -> dict[str, list[DatasetEntry]]:
    grouped: dict[str, list[DatasetEntry]] = {}
    for entry in entries:
        grouped.setdefault(entry.profile_id, []).append(entry)
    return grouped


def load_requested_engine_keys(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier moteurs introuvable: {path}")

    engine_keys: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line not in engine_keys:
            engine_keys.append(line)

    if not engine_keys:
        raise ValueError(f"Aucun moteur liste dans {path}")
    return engine_keys


def build_engine_catalog(
    path: Path, inference_engines_config: Any
) -> list[tuple[str, Any]]:
    requested_engine_keys = load_requested_engine_keys(path)
    catalog: list[tuple[str, Any]] = []

    for engine_key in requested_engine_keys:
        engine_config = inference_engines_config.inference_engines.get(engine_key)
        if engine_config is None:
            raise ValueError(f"Moteur inconnu dans {path}: {engine_key}")
        catalog.append((engine_key, engine_config))

    return sorted(
        catalog,
        key=lambda item: (
            item[1].cost_score if item[1].cost_score is not None else 10**9,
            item[0],
        ),
    )


def build_case_contexts(
    *,
    entries_by_profile: dict[str, list[DatasetEntry]],
    runtime_profiles: dict[str, Any],
    engines: list[tuple[str, Any]],
) -> dict[tuple[str, str], list[CaseEvaluationContext]]:
    contexts_by_pair: dict[tuple[str, str], list[CaseEvaluationContext]] = {}

    for profile_id, entries in entries_by_profile.items():
        runtime_profile = runtime_profiles.get(profile_id)
        if runtime_profile is None:
            raise ValueError(
                f"Profil present dans le dataset mais absent de la config: {profile_id}"
            )

        profile_fingerprint = build_profile_fingerprint(
            prompt_text=runtime_profile.prompt_text,
            criterion_ids=runtime_profile.criterion_ids,
            criterion_weights=runtime_profile.criterion_weights,
            le_few_shot=runtime_profile.le_few_shot,
        )
        merged_params_fingerprint = build_params_fingerprint({})

        for engine_key, engine_config in engines:
            engine_fingerprint = build_engine_fingerprint(
                engine_key=engine_key,
                engine_type=engine_config.type,
                model=engine_config.model,
                base_url=engine_config.base_url,
                timeout_sec=engine_config.timeout_sec,
            )
            contexts_by_pair[(profile_id, engine_key)] = [
                CaseEvaluationContext(
                    entry=entry,
                    cache_key=build_cache_key(
                        case_id=entry.id,
                        text=entry.text,
                        expected_decision=entry.decision_expected,
                        profile_fingerprint=profile_fingerprint,
                        engine_fingerprint=engine_fingerprint,
                        merged_params_fingerprint=merged_params_fingerprint,
                    ),
                    profile_fingerprint=profile_fingerprint,
                    engine_fingerprint=engine_fingerprint,
                    merged_params_fingerprint=merged_params_fingerprint,
                    engine_key=engine_key,
                    engine_type=engine_config.type,
                    cost_score=engine_config.cost_score,
                )
                for entry in entries
            ]

    return contexts_by_pair


def evaluate_case_context(
    *,
    context: CaseEvaluationContext,
    config_dir: Path,
    inference_adapter: DirectInferenceAdapter,
) -> CaseEvaluationRecord:
    evaluated_at = utc_now_iso()
    started_at = time.monotonic()
    muted_output = io.StringIO()

    try:
        with (
            contextlib.redirect_stdout(muted_output),
            contextlib.redirect_stderr(muted_output),
        ):
            result = ANALYZE_TEXT(
                text=context.entry.text,
                profile_id=context.entry.profile_id,
                inference_engine=context.engine_key,
                config_dir=config_dir,
                inference_adapter=inference_adapter,
            )
        elapsed_sec = result.latency_sec
        if elapsed_sec is None:
            elapsed_sec = time.monotonic() - started_at
        return CaseEvaluationRecord(
            cache_key=context.cache_key,
            evaluated_at=evaluated_at,
            case_id=context.entry.id,
            profile_id=context.entry.profile_id,
            text_hash=hash_text(context.entry.text),
            expected_decision=context.entry.decision_expected,
            profile_fingerprint=context.profile_fingerprint,
            engine_fingerprint=context.engine_fingerprint,
            merged_params_fingerprint=context.merged_params_fingerprint,
            engine_key=context.engine_key,
            engine_type=context.engine_type,
            cost_score=context.cost_score,
            model_used=result.model_used,
            actual_decision=result.decision,
            score=result.score,
            band_match=score_matches_expected(
                expected_decision=context.entry.decision_expected,
                actual_score=result.score,
            ),
            exact_match=result.decision == context.entry.decision_expected,
            distance_to_target=distance_to_target(
                expected_decision=context.entry.decision_expected,
                actual_score=result.score,
            ),
            latency_sec=elapsed_sec,
            error=None,
            covered_elements=tuple(result.covered_elements),
            missing_elements=tuple(result.missing_elements),
        )
    except Exception as exc:
        elapsed_sec = time.monotonic() - started_at
        message = str(exc).strip() or exc.__class__.__name__
        return CaseEvaluationRecord(
            cache_key=context.cache_key,
            evaluated_at=evaluated_at,
            case_id=context.entry.id,
            profile_id=context.entry.profile_id,
            text_hash=hash_text(context.entry.text),
            expected_decision=context.entry.decision_expected,
            profile_fingerprint=context.profile_fingerprint,
            engine_fingerprint=context.engine_fingerprint,
            merged_params_fingerprint=context.merged_params_fingerprint,
            engine_key=context.engine_key,
            engine_type=context.engine_type,
            cost_score=context.cost_score,
            model_used=None,
            actual_decision=None,
            score=None,
            band_match=False,
            exact_match=False,
            distance_to_target=None,
            latency_sec=elapsed_sec,
            error=message,
            covered_elements=(),
            missing_elements=(),
        )


def build_attempt_summary(
    *,
    profile_id: str,
    engine_key: str,
    contexts_by_pair: dict[tuple[str, str], list[CaseEvaluationContext]],
    case_results: dict[str, CaseEvaluationRecord],
    threshold: float,
    generated_at: str,
) -> EngineAttempt:
    contexts = contexts_by_pair[(profile_id, engine_key)]
    first_context = contexts[0]
    aligned_records = [case_results.get(context.cache_key) for context in contexts]
    return summarize_engine_attempt(
        generated_at=generated_at,
        profile_id=profile_id,
        engine_key=engine_key,
        engine_type=first_context.engine_type,
        cost_score=first_context.cost_score,
        case_records=aligned_records,
        threshold=threshold,
    )


def select_recommended_engine(
    *,
    profile_id: str,
    engine_keys: list[str],
    contexts_by_pair: dict[tuple[str, str], list[CaseEvaluationContext]],
    case_results: dict[str, CaseEvaluationRecord],
    threshold: float,
    generated_at: str,
) -> EngineAttempt | None:
    attempts_by_engine = {
        engine_key: build_attempt_summary(
            profile_id=profile_id,
            engine_key=engine_key,
            contexts_by_pair=contexts_by_pair,
            case_results=case_results,
            threshold=threshold,
            generated_at=generated_at,
        )
        for engine_key in engine_keys
    }
    return select_recommended_attempt(
        engine_keys=engine_keys,
        attempts_by_engine=attempts_by_engine,
    )


def pending_contexts(
    *,
    contexts: list[CaseEvaluationContext],
    case_results: dict[str, CaseEvaluationRecord],
    refresh: bool,
) -> list[CaseEvaluationContext]:
    if refresh:
        return list(contexts)
    return [context for context in contexts if context.cache_key not in case_results]


def is_systemic_engine_error(message: str | None) -> bool:
    if message is None:
        return False
    normalized = message.strip().lower()
    return any(marker in normalized for marker in SYSTEMIC_ENGINE_ERROR_MARKERS)


def persist_case_record(
    *,
    record: CaseEvaluationRecord,
    case_results: dict[str, CaseEvaluationRecord],
) -> bool:
    if is_systemic_engine_error(record.error):
        return False

    case_results[record.cache_key] = record
    append_case_result(CASE_RESULTS_PATH, record)
    return True


def purge_systemic_error_rows(path: Path) -> int:
    if not path.exists():
        return 0

    kept_lines: list[str] = []
    removed_count = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped_line = raw_line.strip()
        if not stripped_line:
            continue
        payload = json.loads(stripped_line)
        error = payload.get("error")
        if isinstance(error, str) and is_systemic_engine_error(error):
            removed_count += 1
            continue
        kept_lines.append(json.dumps(payload, ensure_ascii=False))

    if removed_count == 0:
        return 0

    path.write_text(
        "\n".join(kept_lines) + ("\n" if kept_lines else ""), encoding="utf-8"
    )
    return removed_count


def evaluate_context_batch(
    *,
    contexts: list[CaseEvaluationContext],
    engine_type: str,
    remote_workers: int,
    inference_adapter: DirectInferenceAdapter,
    case_results: dict[str, CaseEvaluationRecord],
) -> None:
    if not contexts:
        return

    first_context = contexts[0]
    first_record = evaluate_case_context(
        context=first_context,
        config_dir=CONFIG_DIR,
        inference_adapter=inference_adapter,
    )
    persist_case_record(record=first_record, case_results=case_results)
    print(f"  - {first_record.case_id}: {format_case_record(first_record)}")

    if len(contexts) == 1:
        return

    if is_systemic_engine_error(first_record.error):
        print(
            "  - arret anticipe pour ce moteur: erreur fournisseur/systeme detectee, "
            "les cas restants sont ignores pour eviter des appels inutiles"
        )
        return

    remaining_contexts = contexts[1:]

    if engine_type == "local":
        for context in remaining_contexts:
            record = evaluate_case_context(
                context=context,
                config_dir=CONFIG_DIR,
                inference_adapter=inference_adapter,
            )
            persist_case_record(record=record, case_results=case_results)
            print(f"  - {record.case_id}: {format_case_record(record)}")
        return

    with ThreadPoolExecutor(max_workers=max(1, remote_workers)) as executor:
        futures = {
            executor.submit(
                evaluate_case_context,
                context=context,
                config_dir=CONFIG_DIR,
                inference_adapter=inference_adapter,
            ): context
            for context in remaining_contexts
        }
        for future in as_completed(futures):
            record = future.result()
            persist_case_record(record=record, case_results=case_results)
            print(f"  - {record.case_id}: {format_case_record(record)}")


def format_case_record(record: CaseEvaluationRecord) -> str:
    latency_label = "?" if record.latency_sec is None else f"{record.latency_sec:.2f}s"
    if record.error:
        return f"ERROR en {latency_label}: {record.error}"
    band_label = "OK" if record.band_match else "MISS"
    return (
        f"score={record.score} decision={record.actual_decision} "
        f"bande={band_label} en {latency_label}"
    )


def format_attempt(attempt: EngineAttempt) -> str:
    rate_label = f"{attempt.ratio:.0%}"
    avg_latency = (
        "?" if attempt.avg_latency_sec is None else f"{attempt.avg_latency_sec:.2f}s"
    )
    total_latency = (
        "?" if attempt.elapsed_sec is None else f"{attempt.elapsed_sec:.2f}s"
    )
    detail = ""
    if attempt.mismatch_entry_id:
        detail = f" | premier echec: {attempt.mismatch_entry_id}"
    if attempt.error:
        detail = f" | erreur: {attempt.error}"
    return (
        f"{attempt.status_label} {attempt.matched_count}/{attempt.total_count} "
        f"({rate_label}), avg={avg_latency}, total={total_latency}, "
        f"cout={format_optional_int(attempt.cost_score)}{detail}"
    )


def format_optional_int(value: int | None) -> str:
    return "-" if value is None else str(value)


def save_summary_results(path: Path, attempts: list[EngineAttempt]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDNAMES)
        writer.writeheader()
        for attempt in sorted(
            attempts, key=lambda item: (item.profile_id, item.engine_key)
        ):
            writer.writerow(
                {
                    "generated_at": attempt.generated_at or "",
                    "profile_id": attempt.profile_id,
                    "engine_key": attempt.engine_key,
                    "engine_type": attempt.engine_type or "",
                    "status": attempt.status_label,
                    "qualified_threshold": str(attempt.qualified_threshold).lower(),
                    "cost_score": ""
                    if attempt.cost_score is None
                    else str(attempt.cost_score),
                    "elapsed_total_sec": (
                        ""
                        if attempt.elapsed_sec is None
                        else f"{attempt.elapsed_sec:.3f}"
                    ),
                    "avg_latency_sec": (
                        ""
                        if attempt.avg_latency_sec is None
                        else f"{attempt.avg_latency_sec:.3f}"
                    ),
                    "band_match_rate": f"{attempt.ratio:.4f}",
                    "exact_match_rate": (
                        "0.0000"
                        if attempt.total_count == 0
                        else f"{attempt.exact_match_count / attempt.total_count:.4f}"
                    ),
                    "matched_count": str(attempt.matched_count),
                    "exact_match_count": str(attempt.exact_match_count),
                    "evaluated_count": str(attempt.evaluated_count),
                    "total_count": str(attempt.total_count),
                    "error_count": str(attempt.error_count),
                    "error": attempt.error or "",
                    "first_failed_case_id": attempt.mismatch_entry_id or "",
                    "expected_decision": attempt.mismatch_expected or "",
                    "expected_score_band": attempt.mismatch_expected_band or "",
                    "distance_to_target": (
                        ""
                        if attempt.mismatch_distance_to_target is None
                        else str(attempt.mismatch_distance_to_target)
                    ),
                    "actual_score": (
                        ""
                        if attempt.mismatch_actual_score is None
                        else str(attempt.mismatch_actual_score)
                    ),
                    "actual_decision": attempt.mismatch_actual or "",
                    "first_evaluated_at": attempt.first_evaluated_at or "",
                    "last_evaluated_at": attempt.last_evaluated_at or "",
                }
            )


def save_worst_cases(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WORST_CASE_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(cast(Any, row))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Selection minimaliste des moteurs CoVeX"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Seuil minimal de band_match_rate pour recommander un moteur (defaut: 0.8)",
    )
    parser.add_argument(
        "--remote-workers",
        type=int,
        default=DEFAULT_REMOTE_WORKERS,
        help="Nombre max d'appels distants paralleles par moteur (defaut: 4)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Rejoue les cas eligibles meme s'ils existent deja dans le cache JSONL.",
    )
    parser.add_argument(
        "--exhaustive",
        action="store_true",
        help="Evalue tous les moteurs candidats meme si un profil est deja qualifie.",
    )
    args = parser.parse_args()
    if not 0.0 < args.threshold <= 1.0:
        raise SystemExit("--threshold doit etre dans ]0, 1].")
    if args.remote_workers < 1:
        raise SystemExit("--remote-workers doit etre >= 1.")
    return args


def main() -> None:
    args = parse_args()
    purged_rows = purge_systemic_error_rows(CASE_RESULTS_PATH)
    if purged_rows:
        print(
            f"Nettoyage cache: {purged_rows} lignes d'erreurs systemiques retirees de {CASE_RESULTS_PATH.name}"
        )
    dataset_entries = load_dataset_entries(DATASET_PATH)
    entries_by_profile = group_entries_by_profile(dataset_entries)
    runtime_profiles = LOAD_RUNTIME_ANALYSIS_PROFILES(config_dir=CONFIG_DIR)
    inference_engines_config = LOAD_INFERENCE_ENGINES_CONFIG(config_dir=CONFIG_DIR)
    engines = build_engine_catalog(ENGINES_PATH, inference_engines_config)
    engine_keys = [engine_key for engine_key, _engine_config in engines]
    contexts_by_pair = build_case_contexts(
        entries_by_profile=entries_by_profile,
        runtime_profiles=runtime_profiles,
        engines=engines,
    )
    case_results = load_case_results(CASE_RESULTS_PATH)
    inference_adapter = DirectInferenceAdapter(
        config_dir=CONFIG_DIR,
        timeout_sec=TIMEOUT_SEC,
    )
    profiles_with_dataset = [
        profile_id
        for profile_id in sorted(runtime_profiles)
        if entries_by_profile.get(profile_id)
    ]
    generated_at = utc_now_iso()
    remaining_profiles = set(profiles_with_dataset)

    if not args.exhaustive:
        for profile_id in list(remaining_profiles):
            recommended = select_recommended_engine(
                profile_id=profile_id,
                engine_keys=engine_keys,
                contexts_by_pair=contexts_by_pair,
                case_results=case_results,
                threshold=args.threshold,
                generated_at=generated_at,
            )
            if recommended is not None:
                remaining_profiles.discard(profile_id)

    for engine_key, engine_config in engines:
        target_profiles = [
            profile_id
            for profile_id in profiles_with_dataset
            if args.exhaustive or profile_id in remaining_profiles
        ]
        if not target_profiles:
            break

        print(
            f"\n=== Test du moteur {engine_key} "
            f"(type={engine_config.type}, cost_score={engine_config.cost_score}) ==="
        )

        engine_pending_contexts: list[CaseEvaluationContext] = []
        for profile_id in target_profiles:
            contexts = contexts_by_pair[(profile_id, engine_key)]
            pending = pending_contexts(
                contexts=contexts,
                case_results=case_results,
                refresh=args.refresh,
            )
            cached_count = 0 if args.refresh else len(contexts) - len(pending)
            print(
                f"- {profile_id}: {len(pending)} cas a executer, {cached_count} reutilises depuis le cache"
            )
            engine_pending_contexts.extend(pending)

        evaluate_context_batch(
            contexts=engine_pending_contexts,
            engine_type=engine_config.type,
            remote_workers=args.remote_workers,
            inference_adapter=inference_adapter,
            case_results=case_results,
        )

        generated_at = utc_now_iso()
        for profile_id in target_profiles:
            attempt = build_attempt_summary(
                profile_id=profile_id,
                engine_key=engine_key,
                contexts_by_pair=contexts_by_pair,
                case_results=case_results,
                threshold=args.threshold,
                generated_at=generated_at,
            )
            if attempt.evaluated_count == 0:
                continue
            print(f"- {profile_id}: {format_attempt(attempt)}")

        if not args.exhaustive:
            for profile_id in list(remaining_profiles):
                recommended = select_recommended_engine(
                    profile_id=profile_id,
                    engine_keys=engine_keys,
                    contexts_by_pair=contexts_by_pair,
                    case_results=case_results,
                    threshold=args.threshold,
                    generated_at=generated_at,
                )
                if recommended is not None:
                    remaining_profiles.discard(profile_id)

    generated_at = utc_now_iso()
    attempts: list[EngineAttempt] = []
    for profile_id in profiles_with_dataset:
        for engine_key in engine_keys:
            attempt = build_attempt_summary(
                profile_id=profile_id,
                engine_key=engine_key,
                contexts_by_pair=contexts_by_pair,
                case_results=case_results,
                threshold=args.threshold,
                generated_at=generated_at,
            )
            if attempt.evaluated_count == 0:
                continue
            attempts.append(attempt)

    save_summary_results(RESULTS_PATH, attempts)
    save_worst_cases(
        WORST_CASES_PATH,
        build_worst_case_rows(
            generated_at=generated_at,
            case_results=case_results.values(),
        ),
    )

    from tools.research.render_engine_selection_report import (  # noqa: E402
        attempt_sort_key,
        render_report,
    )

    REPORT_PATH.write_text(render_report(attempts), encoding="utf-8")

    print("\n=== Selection finale ===")
    attempts_by_profile: dict[str, dict[str, EngineAttempt]] = {}
    for attempt in attempts:
        attempts_by_profile.setdefault(attempt.profile_id, {})[attempt.engine_key] = (
            attempt
        )

    for profile_id in profiles_with_dataset:
        recommended = select_recommended_attempt(
            engine_keys=engine_keys,
            attempts_by_engine=attempts_by_profile.get(profile_id, {}),
        )
        if recommended is not None:
            print(
                f"- {profile_id}: moteur recommande = {recommended.engine_key} "
                f"({recommended.ratio:.0%}, cout {format_optional_int(recommended.cost_score)})"
            )
            continue

        attempted = list(attempts_by_profile.get(profile_id, {}).values())
        if not attempted:
            print(f"- {profile_id}: aucun resultat exploitable")
            continue

        best_observed = sorted(attempted, key=attempt_sort_key)[0]
        print(
            f"- {profile_id}: aucun moteur recommande, meilleur observe = "
            f"{best_observed.engine_key} ({best_observed.ratio:.0%})"
        )

    print(f"\nSeuil de recommandation: {args.threshold:.0%}")
    print(f"Cache case-level: {CASE_RESULTS_PATH}")
    print(f"Synthese par profil/moteur: {RESULTS_PATH}")
    print(f"Pires cas: {WORST_CASES_PATH}")
    print(f"Rapport: {REPORT_PATH}")


if __name__ == "__main__":
    main()
