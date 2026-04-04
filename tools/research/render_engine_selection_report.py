"""
Render a Markdown report from aggregate engine selection results.

Execution from the repository root:
- `uv run --project backend python tools/research/render_engine_selection_report.py`
- Reads `artifacts/evaluation/engine_selection_results.csv` and rewrites
  `artifacts/evaluation/engine_selection_report.md`.
"""

from __future__ import annotations

import csv
from pathlib import Path
import sys

SCRIPT_PATH = Path(__file__).resolve()
ROOT_DIR = SCRIPT_PATH.parents[2]
ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "evaluation"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.evaluation.evaluation_models import (  # noqa: E402
    EngineAttempt,
    coerce_optional_bool,
    coerce_optional_float,
    coerce_optional_int,
    coerce_optional_str,
)

RESULTS_PATH = ARTIFACTS_DIR / "engine_selection_results.csv"
REPORT_PATH = ARTIFACTS_DIR / "engine_selection_report.md"
QUALIFICATION_LABEL = "90%"


def load_attempts(path: Path) -> list[EngineAttempt]:
    attempts: list[EngineAttempt] = []
    if not path.exists():
        return attempts

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total_count = int((row.get("total_count") or "0").strip())
            attempts.append(
                EngineAttempt(
                    engine_key=(row.get("engine_key") or "").strip(),
                    cost_score=coerce_optional_int(row.get("cost_score")),
                    elapsed_sec=coerce_optional_float(row.get("elapsed_total_sec")),
                    matched_count=int((row.get("matched_count") or "0").strip()),
                    total_count=total_count,
                    profile_id=(row.get("profile_id") or "").strip(),
                    engine_type=coerce_optional_str(row.get("engine_type")),
                    error=coerce_optional_str(row.get("error")),
                    mismatch_entry_id=coerce_optional_str(
                        row.get("first_failed_case_id")
                    ),
                    mismatch_expected=coerce_optional_str(row.get("expected_decision")),
                    mismatch_expected_band=coerce_optional_str(
                        row.get("expected_score_band")
                    ),
                    mismatch_distance_to_target=coerce_optional_int(
                        row.get("distance_to_target")
                    ),
                    mismatch_actual_score=coerce_optional_int(row.get("actual_score")),
                    mismatch_actual=coerce_optional_str(row.get("actual_decision")),
                    band_match_rate=coerce_optional_float(row.get("band_match_rate")),
                    avg_latency_sec=coerce_optional_float(row.get("avg_latency_sec")),
                    error_count=int((row.get("error_count") or "0").strip()),
                    exact_match_count=int(
                        (row.get("exact_match_count") or "0").strip()
                    ),
                    evaluated_count=int((row.get("evaluated_count") or "0").strip()),
                    generated_at=coerce_optional_str(row.get("generated_at")),
                    first_evaluated_at=coerce_optional_str(
                        row.get("first_evaluated_at")
                    ),
                    last_evaluated_at=coerce_optional_str(row.get("last_evaluated_at")),
                    qualified_threshold=bool(
                        coerce_optional_bool(row.get("qualified_threshold"))
                    ),
                )
            )
    return attempts


def attempt_sort_key(attempt: EngineAttempt) -> tuple[int, int, float, int, float, str]:
    if attempt.qualified_threshold:
        return (
            0,
            attempt.cost_score if attempt.cost_score is not None else 10**9,
            -attempt.ratio,
            attempt.distance,
            attempt.avg_latency_sec if attempt.avg_latency_sec is not None else 10**9,
            attempt.engine_key,
        )
    return (
        1,
        10**9,
        -attempt.ratio,
        attempt.distance,
        attempt.avg_latency_sec if attempt.avg_latency_sec is not None else 10**9,
        attempt.engine_key,
    )


def render_report(attempts: list[EngineAttempt]) -> str:
    by_profile: dict[str, list[EngineAttempt]] = {}
    engine_stats: dict[str, dict[str, float]] = {}
    for attempt in attempts:
        by_profile.setdefault(attempt.profile_id, []).append(attempt)
        stats = engine_stats.setdefault(
            attempt.engine_key,
            {
                "profiles": 0,
                "qualified": 0,
                "matches": 0,
                "total": 0,
                "distance": 0,
            },
        )
        stats["profiles"] += 1
        stats["qualified"] += int(attempt.qualified_threshold)
        stats["matches"] += attempt.matched_count
        stats["total"] += attempt.total_count
        stats["distance"] += attempt.mismatch_distance_to_target or 0

    profile_summaries: list[
        tuple[str, EngineAttempt, list[EngineAttempt], EngineAttempt | None]
    ] = []
    for profile_id, profile_attempts in by_profile.items():
        ordered = sorted(profile_attempts, key=attempt_sort_key)
        recommended = next(
            (attempt for attempt in ordered if attempt.qualified_threshold),
            None,
        )
        profile_summaries.append((profile_id, ordered[0], ordered, recommended))

    profile_summaries.sort(key=lambda item: attempt_sort_key(item[1]) + (item[0],))

    ranked_engines = sorted(
        engine_stats.items(),
        key=lambda item: (
            -item[1]["qualified"],
            -(0.0 if item[1]["total"] == 0 else item[1]["matches"] / item[1]["total"]),
            item[1]["distance"],
            item[0],
        ),
    )

    latest_generated_at = max(
        (attempt.generated_at for attempt in attempts if attempt.generated_at),
        default="-",
    )
    lines = [
        "# Rapport benchmark brain engines",
        "",
        f"- Source CSV: `{RESULTS_PATH.name}`",
        f"- Genere le: {latest_generated_at}",
        f"- Seuil de recommandation: {QUALIFICATION_LABEL}",
        f"- Profils analyses: {len(profile_summaries)}",
        f"- Moteurs compares: {len(engine_stats)}",
        f"- Profils qualifies: {sum(1 for _, _, _, recommended in profile_summaries if recommended is not None)}/{len(profile_summaries)}",
        "- Pires cas exportes dans `engine_worst_cases.csv`.",
        "",
        "## Vue rapide par profil",
        "",
        "| Profil | Recommandation | Statut | Cout | Bandes | Latence moy | Detail |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]

    for profile_id, best, _ordered, recommended in profile_summaries:
        chosen = recommended or best
        recommendation_label = (
            "-" if recommended is None else f"`{recommended.engine_key}`"
        )
        lines.append(
            f"| `{profile_id}` | {recommendation_label} | {chosen.status_label} | {format_int(chosen.cost_score)} | "
            f"{chosen.matched_count}/{chosen.total_count} ({chosen.ratio:.0%}) | {format_elapsed(chosen.avg_latency_sec)} | {format_detail(chosen)} |"
        )

    lines.extend(
        [
            "",
            "## Vue par moteur",
            "",
            "| Moteur | Profils qualifies | Taux cumule | Distance cumulee |",
            "| --- | ---: | ---: | ---: |",
        ]
    )

    for engine_key, stats in ranked_engines:
        ratio = 0.0 if stats["total"] == 0 else stats["matches"] / stats["total"]
        lines.append(
            f"| `{engine_key}` | {int(stats['qualified'])}/{int(stats['profiles'])} | {ratio:.0%} | {int(stats['distance'])} |"
        )

    lines.append("")
    lines.append("## Detail par profil")
    lines.append("")

    for profile_id, best, ordered, recommended in profile_summaries:
        lines.append(f"### `{profile_id}`")
        lines.append("")
        if recommended is None:
            lines.append(
                f"- Aucun moteur ne passe le seuil {QUALIFICATION_LABEL}. Meilleur observe: `{best.engine_key}` | statut `{best.status_label}` | cout {format_int(best.cost_score)} | bandes {best.matched_count}/{best.total_count} ({best.ratio:.0%})"
            )
        else:
            lines.append(
                f"- Moteur recommande: `{recommended.engine_key}` | statut `{recommended.status_label}` | cout {format_int(recommended.cost_score)} | bandes {recommended.matched_count}/{recommended.total_count} ({recommended.ratio:.0%})"
            )
        lines.append("")
        lines.append(
            "| Moteur | Statut | Bandes | Temps total | Latence moy | Cout | Detail |"
        )
        lines.append("| --- | --- | ---: | ---: | ---: | ---: | --- |")
        for attempt in ordered:
            lines.append(
                f"| `{attempt.engine_key}` | {attempt.status_label} | {attempt.matched_count}/{attempt.total_count} ({attempt.ratio:.0%}) | {format_elapsed(attempt.elapsed_sec)} | {format_elapsed(attempt.avg_latency_sec)} | {format_int(attempt.cost_score)} | {format_detail(attempt)} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def format_detail(attempt: EngineAttempt) -> str:
    if attempt.qualified_threshold and not attempt.success:
        return f"Qualifie au seuil {QUALIFICATION_LABEL}"
    if attempt.success:
        return "Tous les cas passent dans la bande attendue"
    if not attempt.complete:
        return f"Execution incomplete: {attempt.evaluated_count}/{attempt.total_count} cas evalues"
    if attempt.error:
        return attempt.error.replace("|", "/")
    if attempt.mismatch_entry_id is None:
        return "Aucun detail disponible"
    return (
        f"{attempt.mismatch_entry_id}: attendu {attempt.mismatch_expected} "
        f"({attempt.mismatch_expected_band}), score {format_int(attempt.mismatch_actual_score)}, "
        f"obtenu {attempt.mismatch_actual}"
    ).replace("|", "/")


def format_elapsed(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}s"


def format_int(value: int | None) -> str:
    return "-" if value is None else str(value)


def main() -> None:
    if not RESULTS_PATH.exists():
        print(f"Source CSV absent, rapport conserve: {RESULTS_PATH}")
        return

    attempts = load_attempts(RESULTS_PATH)
    REPORT_PATH.write_text(render_report(attempts), encoding="utf-8")
    print(f"Rapport genere: {REPORT_PATH}")


if __name__ == "__main__":
    main()
