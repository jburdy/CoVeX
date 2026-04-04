"""
Construit la page NiceGUI du Playground et gere le golden dataset utilise par l'UI.

Usage:
- Module importe par `playground/src/app.py` pour declarer la page `/`.
- Reutilise aussi par les tests playground pour valider les actions UI et le parsing dataset.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from nicegui import ui

from api_client import AnalyzeResult, ApiClient, ApiClientError

CONFIG_DIRECTORY = "config"
DATASETS_DIRECTORY = "datasets"
INFERENCE_ENGINES_FILE = "inference_engines.yaml"
ANALYSIS_PROFILES_FILE = "analysis_profiles.yaml"
GOLDEN_DATASET_FILE = "golden_dataset.jsonl"
PLAYGROUND_TAG = "playground"

FEEDBACK_LABEL_BASE_CLASSES = (
    "q-mt-sm text-body1 text-weight-medium rounded-borders q-px-md q-py-sm"
)
FEEDBACK_LABEL_LOADING_CLASS = "covex-feedback-loading"

DECISION_COLOR_MAP = {
    "KO": "negative",
    "PARTIEL": "warning",
    "OK": "positive",
}


@dataclass(frozen=True)
class PlaygroundControls:
    textarea: Any
    profile_select: Any
    inference_engine_select: Any
    inference_engine_help_label: Any
    submit_button: Any
    sample_buttons: list[Any]
    examples_expansion: Any
    feedback_label: Any
    score_label: Any
    decision_badge: Any
    covered_elements_container: Any
    missing_elements_container: Any
    technical_details_label: Any
    result_live_region: Any


@dataclass
class PlaygroundState:
    text: str = ""
    selected_profile_id: str | None = None
    selected_inference_engine: str | None = None
    is_submitting: bool = False
    validation_message: str = ""
    last_result: AnalyzeResult | None = None
    profile_engine_map: dict[str, str] = field(default_factory=dict)
    inference_engine_details_map: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class GoldenDatasetEntry:
    id: str
    profile_id: str
    text: str
    decision_expected: str
    tags: tuple[str, ...]
    work_note: str | None = None
    extra_fields: dict[str, object] = field(default_factory=dict, compare=False)


def build_playground_page(api_client: ApiClient | None = None) -> PlaygroundState:
    client = api_client or ApiClient()
    state = PlaygroundState()

    ui.add_head_html(
        """
        <style>
        .covex-feedback-loading {
            color: #8a5a00;
            background: linear-gradient(90deg, #fff4c2 0%, #ffe08a 50%, #fff4c2 100%);
            background-size: 200% 100%;
            animation: covex-feedback-pulse 1.1s ease-in-out infinite;
            box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.35);
        }

        .covex-example-group {
            padding: 0.65rem 0.8rem;
            border: 1px solid #d9dee7;
            border-radius: 0.9rem;
            background: linear-gradient(180deg, #fcfdff 0%, #f5f8fc 100%);
        }

        .covex-example-link {
            display: inline-flex;
            align-items: center;
            min-height: 2rem;
            padding: 0.3rem 0.65rem;
            border-radius: 999px;
            border: 1px solid transparent;
            text-decoration: none;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .covex-example-link:hover,
        .covex-example-link:focus-visible {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
        }

        .covex-example-link-ko {
            color: #8a1c1c;
            background: #fff1f1;
            border-color: #f5c2c2;
        }

        .covex-example-link-partiel {
            color: #8a5a00;
            background: #fff6df;
            border-color: #f3d38a;
        }

        .covex-example-link-ok {
            color: #0d5f46;
            background: #edf9f3;
            border-color: #b8e2cc;
        }

        @keyframes covex-feedback-pulse {
            0%,
            100% {
                opacity: 1;
                transform: scale(1);
                background-position: 0% 50%;
                box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.18);
            }

            50% {
                opacity: 0.45;
                transform: scale(1.02);
                background-position: 100% 50%;
                box-shadow: 0 0 0 10px rgba(245, 158, 11, 0);
            }
        }
        </style>
        """
    )

    profile_options = load_profile_options_from_config()

    inference_engine_options, default_inference_engine = load_inference_engine_options()
    state.profile_engine_map = load_profile_inference_engine_map()
    state.inference_engine_details_map = load_inference_engine_details_map()
    playground_examples = list_playground_examples(
        allowed_profile_ids=set(profile_options),
    )

    with ui.card().classes("w-full max-w-3xl mx-auto q-mt-lg"):
        _build_nav_row(ui)

        ui.label("Analyse CoVeX").classes("text-h5")

        async def on_submit() -> None:
            await _handle_submit(state=state, controls=controls, api_client=client)

        def on_profile_change(event: Any) -> None:
            selected_profile_id = getattr(event, "value", None)
            state.selected_profile_id = selected_profile_id
            _sync_inference_engine_for_profile(
                state=state,
                controls=controls,
                profile_to_inference_engine=state.profile_engine_map,
                inference_engine_details_map=state.inference_engine_details_map,
                default_inference_engine=default_inference_engine,
            )

        def on_inference_engine_change(event: Any) -> None:
            selected_inference_engine = _normalize_optional_selection(getattr(event, "value", None))
            state.selected_inference_engine = selected_inference_engine
            _update_inference_engine_help(
                controls=controls,
                selected_inference_engine=selected_inference_engine,
                inference_engine_details_map=state.inference_engine_details_map,
                default_inference_engine=default_inference_engine,
            )

        controls = create_playground_controls(
            ui_module=ui,
            profile_options=profile_options,
            inference_engine_options=inference_engine_options,
            default_inference_engine=default_inference_engine,
            inference_engine_details_map=state.inference_engine_details_map,
            playground_examples=playground_examples,
            initial_profile_id=state.selected_profile_id,
            on_submit=on_submit,
            on_profile_change=on_profile_change,
            on_inference_engine_change=on_inference_engine_change,
            on_select_example=lambda example: _apply_playground_example(
                state=state,
                controls=controls,
                example=example,
            ),
        )

        if not profile_options:
            _set_feedback_message(
                controls,
                "Aucun profil d'analyse disponible pour lancer une analyse.",
            )

    controls.textarea.bind_value(state, "text")
    controls.inference_engine_select.bind_value(state, "selected_inference_engine")

    return state


def build_golden_dataset_page() -> None:
    dataset_path = _resolve_default_dataset_path()

    try:
        entries = load_golden_dataset_entries(dataset_path=dataset_path)
        load_error: str | None = None
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        entries = []
        load_error = str(exc)

    with ui.card().classes("w-full max-w-6xl mx-auto q-mt-lg"):
        _build_nav_row(ui)

        ui.label("Golden dataset").classes("text-h5")
        ui.label(f"Fichier : {dataset_path}  •  {len(entries)} entrees").classes(
            "text-caption text-grey-7 q-mb-sm"
        )

        if load_error:
            ui.label(f"Impossible de charger le dataset : {load_error}").classes(
                "text-body1 text-negative"
            )
            return

        if not entries:
            ui.label("Aucune entree dans le dataset.").classes("text-body1 text-grey-7")
            return

        _render_golden_dataset_table(ui, entries)


def _render_golden_dataset_table(ui_module: Any, entries: list[GoldenDatasetEntry]) -> None:
    """Affiche les entrees du golden dataset via ui.table sans pagination."""
    columns = [
        {"name": "id", "label": "ID", "field": "id", "align": "left", "sortable": True},
        {
            "name": "profile_id",
            "label": "Profil",
            "field": "profile_id",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "decision_expected",
            "label": "Decision",
            "field": "decision_expected",
            "align": "left",
            "sortable": True,
        },
        {"name": "tags", "label": "Tags", "field": "tags", "align": "left"},
        {"name": "text", "label": "Texte", "field": "text", "align": "left"},
    ]
    rows = [
        {
            "id": entry.id,
            "profile_id": entry.profile_id,
            "decision_expected": entry.decision_expected.strip().upper(),
            "tags": ", ".join(entry.tags),
            "text": entry.text,
        }
        for entry in entries
    ]

    table = ui_module.table(
        columns=columns,
        rows=rows,
        row_key="id",
        pagination={"rowsPerPage": 0},
    ).classes("w-full")

    table.add_slot(
        "body-cell-decision_expected",
        """
        <q-td :props="props">
            <q-badge
                :color="props.value === 'OK' ? 'positive' : props.value === 'PARTIEL' ? 'warning' : 'negative'"
                :label="props.value"
                outline
            />
        </q-td>
        """,
    )
    table.add_slot(
        "body-cell-text",
        """
        <q-td :props="props" style="white-space: pre-wrap; max-width: 40rem; word-break: break-word;">
            {{ props.value }}
        </q-td>
        """,
    )


def create_playground_controls(
    *,
    ui_module: Any,
    profile_options: dict[str, str],
    inference_engine_options: dict[str, str],
    default_inference_engine: str | None,
    inference_engine_details_map: dict[str, str],
    playground_examples: list[GoldenDatasetEntry],
    initial_profile_id: str | None,
    on_submit: Any,
    on_profile_change: Any,
    on_inference_engine_change: Any,
    on_select_example: Any,
) -> PlaygroundControls:
    profile_select = (
        ui_module.select(
            label="Profil d'analyse",
            options=profile_options,
            value=initial_profile_id,
            on_change=on_profile_change,
        )
        .props("tabindex=1 aria-label='Profil d'analyse profile_id'")
        .classes("w-full focus-visible:outline focus-visible:outline-2")
    )

    inference_engine_label = "Moteur d'inference"

    inference_engine_select = (
        ui_module.select(
            label=inference_engine_label,
            options=inference_engine_options,
            value=None,
            on_change=on_inference_engine_change,
        )
        .props("clearable tabindex=2 aria-label='Moteur d'inference inference_engine'")
        .classes("w-full focus-visible:outline focus-visible:outline-2")
    )
    inference_engine_help_label = ui_module.label(
        _format_inference_engine_help(
            selected_inference_engine=None,
            inference_engine_details_map=inference_engine_details_map,
            default_inference_engine=default_inference_engine,
        )
    ).classes("text-caption text-grey-8")

    textarea = (
        ui_module.textarea(label="Texte source")
        .props("autogrow clearable tabindex=3 aria-label='Texte source text'")
        .classes("w-full focus-visible:outline focus-visible:outline-2")
    )

    with ui_module.row().classes("w-full flex flex-wrap gap-2 items-center"):
        submit_button = (
            ui_module.button("Lancer l'analyse", on_click=on_submit)
            .props("color=primary unelevated no-caps tabindex=4 aria-label='Lancer l'analyse'")
            .classes("w-full sm:w-auto focus-visible:outline focus-visible:outline-2")
            .style("min-height: 44px; min-width: 44px")
        )

    sample_buttons: list[Any] = []
    examples_expansion = (
        ui_module.expansion(
            "Exemples de saisie par profil d'analyse",
            value=True,
        )
        .props("icon=edit_note header-class='rounded-borders bg-grey-2 text-primary q-pa-sm'")
        .classes("w-full q-mt-sm cursor-pointer")
    )
    with examples_expansion:
        ui_module.label(
            "Chaque profil propose maintenant un parcours progressif: KO, PARTIEL puis OK."
        ).classes("text-caption text-grey-7 q-mb-sm")
        for profile_id, profile_name, profile_examples in group_playground_examples(
            playground_examples=playground_examples,
            profile_options=profile_options,
        ):
            with ui_module.column().classes("w-full gap-2 q-mb-sm covex-example-group"):
                ui_module.label(profile_name).classes("text-subtitle2")
                with ui_module.row().classes("w-full flex flex-wrap items-center gap-2"):
                    for example in profile_examples:
                        prefix, emoji = _format_playground_example_decision(
                            example.decision_expected
                        )
                        link_label = f"{emoji} {_format_playground_example_label(example)}"
                        link_class = _format_playground_example_link_class(
                            example.decision_expected
                        )
                        sample_link = (
                            ui_module.link(link_label, "#")
                            .props(
                                f"aria-label='Charger exemple {prefix.lower()} {example.id.lower()}' "
                                f"title='{link_label}'"
                            )
                            .classes(f"text-body2 covex-example-link {link_class}")
                            .style("cursor: pointer")
                        )
                        sample_link.on(
                            "click.prevent",
                            lambda _event, e=example: _handle_example_selection(
                                ui_module=ui_module,
                                examples_expansion=examples_expansion,
                                on_select_example=on_select_example,
                                example=e,
                            ),
                        )
                        sample_buttons.append(sample_link)

    feedback_label = ui_module.label("").classes(FEEDBACK_LABEL_BASE_CLASSES)

    with ui_module.card().classes("q-mt-md w-full"):
        with ui_module.column().classes("gap-3"):
            score_label = ui_module.label("Score: --")
            decision_badge = ui_module.badge("Decision: --", color="warning")
            _set_element_visibility(decision_badge, False)
            with ui_module.row().classes("w-full gap-4 flex-wrap items-stretch"):
                covered_elements_container = ui_module.column().classes("w-full gap-1")
                _render_covered_elements_table(
                    ui_module=ui_module,
                    container=covered_elements_container,
                    covered_elements=(),
                    extractions=(),
                )
                missing_elements_container = ui_module.column().classes("w-full gap-1")
                _render_missing_elements_list(
                    ui_module=ui_module,
                    container=missing_elements_container,
                    elements=(),
                )
            result_live_region = (
                ui_module.label("").props("role=status aria-live=polite").classes("sr-only")
            )

    with ui_module.card().classes("q-mt-md w-full"):
        with ui_module.column().classes("gap-1"):
            ui_module.label("Metadonnees techniques").classes("text-subtitle2")
            technical_details_label = ui_module.label("-").classes("whitespace-pre-line")

    return PlaygroundControls(
        textarea=textarea,
        profile_select=profile_select,
        inference_engine_select=inference_engine_select,
        inference_engine_help_label=inference_engine_help_label,
        submit_button=submit_button,
        sample_buttons=sample_buttons,
        examples_expansion=examples_expansion,
        feedback_label=feedback_label,
        score_label=score_label,
        decision_badge=decision_badge,
        covered_elements_container=covered_elements_container,
        missing_elements_container=missing_elements_container,
        technical_details_label=technical_details_label,
        result_live_region=result_live_region,
    )


def normalize_text(raw_text: str) -> str:
    return raw_text.strip()


def load_profile_options_from_config(*, config_dir: Path | None = None) -> dict[str, str]:
    payload = _load_yaml_config(ANALYSIS_PROFILES_FILE, config_dir=config_dir)
    if payload is None:
        return {}
    return build_profile_options_from_config_payload(payload)


def build_profile_options_from_config_payload(payload: dict[str, object]) -> dict[str, str]:
    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, dict):
        return {}

    options: dict[str, str] = {}
    for profile_id, raw_profile in raw_profiles.items():
        if not isinstance(profile_id, str):
            continue

        normalized_profile_id = profile_id.strip()
        if not normalized_profile_id:
            continue

        profile_name = normalized_profile_id
        if isinstance(raw_profile, dict):
            raw_name = raw_profile.get("name")
            if isinstance(raw_name, str) and raw_name.strip():
                profile_name = raw_name.strip()

        options[normalized_profile_id] = profile_name

    return options

    options: dict[str, str] = {}
    for profile_id, raw_profile in raw_profiles.items():
        if not isinstance(profile_id, str):
            continue

        normalized_profile_id = profile_id.strip()
        if not normalized_profile_id:
            continue

        profile_name = normalized_profile_id
        if isinstance(raw_profile, dict):
            raw_name = raw_profile.get("name")
            if isinstance(raw_name, str) and raw_name.strip():
                profile_name = raw_name.strip()

        options[normalized_profile_id] = profile_name

    return options


def group_playground_examples(
    *,
    playground_examples: list[GoldenDatasetEntry],
    profile_options: dict[str, str],
) -> list[tuple[str, str, list[GoldenDatasetEntry]]]:
    grouped_examples: dict[str, list[GoldenDatasetEntry]] = {}
    profile_order: list[str] = []

    for profile_id in profile_options:
        grouped_examples[profile_id] = []
        profile_order.append(profile_id)

    for example in playground_examples:
        profile_id = example.profile_id.strip()
        if not profile_id:
            continue
        if profile_id not in grouped_examples:
            grouped_examples[profile_id] = []
            profile_order.append(profile_id)
        grouped_examples[profile_id].append(example)

    return [
        (
            profile_id,
            profile_options.get(profile_id, profile_id),
            _sort_playground_examples(grouped_examples[profile_id]),
        )
        for profile_id in profile_order
        if grouped_examples[profile_id]
    ]


def _handle_example_selection(
    *,
    ui_module: Any,
    examples_expansion: Any,
    on_select_example: Any,
    example: GoldenDatasetEntry,
) -> None:
    on_select_example(example)
    if hasattr(examples_expansion, "close"):
        if hasattr(ui_module, "timer"):
            ui_module.timer(0, examples_expansion.close, once=True)
        else:
            examples_expansion.close()


def load_inference_engine_options(
    *, config_dir: Path | None = None
) -> tuple[dict[str, str], str | None]:
    payload = _load_yaml_config(INFERENCE_ENGINES_FILE, config_dir=config_dir)
    if payload is None:
        return {}, None
    return build_inference_engine_options(payload)


def load_profile_inference_engine_map(*, config_dir: Path | None = None) -> dict[str, str]:
    payload = _load_yaml_config(ANALYSIS_PROFILES_FILE, config_dir=config_dir)
    if payload is None:
        return {}
    return build_profile_inference_engine_map(payload)


def build_inference_engine_options(payload: dict[str, object]) -> tuple[dict[str, str], str | None]:
    default_inference_engine = payload.get("default_inference_engine")
    default_key = default_inference_engine if isinstance(default_inference_engine, str) else None
    parsed = _parse_inference_engines(payload)

    options: dict[str, str] = {}
    for key, _model, _engine_type, _cost_score, justification in parsed:
        label = key
        if justification:
            label = f"{label} - {justification}"
        options[key] = label

    return options, default_key


def load_inference_engine_details_map(*, config_dir: Path | None = None) -> dict[str, str]:
    payload = _load_yaml_config(INFERENCE_ENGINES_FILE, config_dir=config_dir)
    if payload is None:
        return {}
    return build_inference_engine_details_map(payload)


def build_inference_engine_details_map(payload: dict[str, object]) -> dict[str, str]:
    del payload
    return {}


def _parse_inference_engines(
    payload: dict[str, object],
) -> list[tuple[str, str, str, int | None, str]]:
    """Convertit le YAML `inference_engines` en tuples (cle, modele, type, cout, justification)."""
    raw_inference_engines = payload.get("inference_engines")
    if not isinstance(raw_inference_engines, dict):
        return []

    results: list[tuple[str, str, str, int | None, str]] = []
    for key, raw_config in raw_inference_engines.items():
        if not isinstance(key, str) or not key.strip():
            continue

        model = ""
        engine_type = ""
        cost_score: int | None = None
        justification = ""
        if isinstance(raw_config, dict):
            raw_model = raw_config.get("model")
            raw_engine_type = raw_config.get("type")
            raw_cost_score = raw_config.get("cost_score")
            raw_justification = raw_config.get("justification")
            if isinstance(raw_model, str):
                model = raw_model.strip()
            if isinstance(raw_engine_type, str):
                engine_type = raw_engine_type.strip()
            if isinstance(raw_cost_score, int):
                cost_score = raw_cost_score
            if isinstance(raw_justification, str):
                justification = raw_justification.strip()

        results.append((key, model, engine_type, cost_score, justification))
    return results


def _format_inference_engine_help(
    *,
    selected_inference_engine: str | None,
    inference_engine_details_map: dict[str, str],
    default_inference_engine: str | None,
) -> str:
    del selected_inference_engine, inference_engine_details_map, default_inference_engine
    return ""


def _update_inference_engine_help(
    *,
    controls: PlaygroundControls | Any,
    selected_inference_engine: str | None,
    inference_engine_details_map: dict[str, str],
    default_inference_engine: str | None,
) -> None:
    controls.inference_engine_help_label.text = _format_inference_engine_help(
        selected_inference_engine=selected_inference_engine,
        inference_engine_details_map=inference_engine_details_map,
        default_inference_engine=default_inference_engine,
    )
    if hasattr(controls.inference_engine_help_label, "update"):
        controls.inference_engine_help_label.update()


def build_profile_inference_engine_map(payload: dict[str, object]) -> dict[str, str]:
    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, dict):
        return {}

    profile_engine_map: dict[str, str] = {}
    for profile_id, raw_profile in raw_profiles.items():
        if not isinstance(profile_id, str) or not profile_id.strip():
            continue
        if not isinstance(raw_profile, dict):
            continue

        inference_engine_key = raw_profile.get("inference_engine_key")
        if not isinstance(inference_engine_key, str):
            continue

        normalized_inference_engine_key = inference_engine_key.strip()
        if not normalized_inference_engine_key:
            continue
        profile_engine_map[profile_id] = normalized_inference_engine_key

    return profile_engine_map


def validate_submission(text: str, selected_profile_id: str | None) -> str:
    if not normalize_text(text):
        return "Veuillez saisir un texte avant de lancer l'analyse."
    if not selected_profile_id or not selected_profile_id.strip():
        return "Veuillez selectionner un profil d'analyse avant de lancer l'analyse."
    return ""


def build_analyze_payload(
    *,
    text: str,
    selected_profile_id: str,
    selected_inference_engine: str | None = None,
) -> dict[str, str]:
    payload = {"text": normalize_text(text), "profile_id": selected_profile_id}
    inference_engine = _normalize_optional_selection(selected_inference_engine)
    if inference_engine is not None:
        payload["inference_engine"] = inference_engine
    return payload


def prepare_submission(state: PlaygroundState) -> tuple[bool, dict[str, str]]:
    validation_message = validate_submission(state.text, state.selected_profile_id)
    if validation_message:
        state.validation_message = validation_message
        return False, {}

    state.validation_message = ""
    selected_profile_id = state.selected_profile_id or ""
    return True, build_analyze_payload(
        text=state.text,
        selected_profile_id=selected_profile_id,
        selected_inference_engine=state.selected_inference_engine,
    )


def get_decision_color(decision: str) -> str:
    return DECISION_COLOR_MAP.get(decision, "warning")


def load_golden_dataset_entries(*, dataset_path: Path | None = None) -> list[GoldenDatasetEntry]:
    path = dataset_path or _resolve_default_dataset_path()
    entries: list[GoldenDatasetEntry] = []
    seen_ids: set[str] = set()

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped_line = raw_line.strip()
            if not stripped_line:
                continue

            payload = json.loads(stripped_line)
            if not isinstance(payload, dict):
                raise ValueError(f"Ligne {line_number} invalide dans {path}")

            entry = _build_golden_dataset_entry(payload, line_number=line_number, path=path)
            if entry.id in seen_ids:
                raise ValueError(f"Identifiant duplique dans {path}: {entry.id}")
            seen_ids.add(entry.id)
            entries.append(entry)

    return entries


def list_playground_examples(
    *,
    dataset_path: Path | None = None,
    allowed_profile_ids: set[str] | None = None,
) -> list[GoldenDatasetEntry]:
    try:
        entries = load_golden_dataset_entries(dataset_path=dataset_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return []

    return [
        entry
        for entry in entries
        if PLAYGROUND_TAG in entry.tags
        and (allowed_profile_ids is None or entry.profile_id in allowed_profile_ids)
    ]


async def _handle_submit(*, state: PlaygroundState, controls, api_client: ApiClient) -> None:
    if state.is_submitting:
        return

    is_valid, payload = prepare_submission(state)
    if not is_valid:
        _set_feedback_message(controls, state.validation_message)
        controls.technical_details_label.text = "--"
        return

    state.is_submitting = True
    controls.submit_button.disable()
    _set_feedback_message(controls, "Analyse en cours de traitement...", is_loading=True)
    controls.technical_details_label.text = "calcul en cours..."
    await asyncio.sleep(0)

    try:
        state.last_result = await asyncio.to_thread(
            api_client.analyze,
            text=payload["text"],
            profile_id=payload["profile_id"],
            inference_engine=payload.get("inference_engine"),
        )
        _render_result(state=state, controls=controls, result=state.last_result)
        _set_feedback_message(controls, "Analyse terminee. Resultat mis a jour.")
    except ApiClientError as exc:
        _set_feedback_message(controls, _map_api_error_message(exc))
        controls.technical_details_label.text = _format_api_error_details(exc)
    finally:
        state.is_submitting = False
        controls.submit_button.enable()


def _set_feedback_message(
    controls: PlaygroundControls, message: str, *, is_loading: bool = False
) -> None:
    controls.feedback_label.text = message
    if is_loading:
        controls.feedback_label.classes(add=FEEDBACK_LABEL_LOADING_CLASS)
    else:
        controls.feedback_label.classes(remove=FEEDBACK_LABEL_LOADING_CLASS)


def _map_api_error_message(exc: ApiClientError) -> str:
    if exc.status_code == 400:
        return exc.raw_message or "Requete invalide. Verifiez le texte saisi."
    if exc.status_code == 404:
        return exc.raw_message or "Profil d'analyse introuvable. Selectionnez un autre profil."
    if exc.status_code == 503:
        return exc.raw_message or "Service temporairement indisponible. Reessayez."
    return exc.raw_message or "Erreur interne temporaire. Reessayez."


def _format_api_error_details(exc: ApiClientError) -> str:
    lines = ["non disponible"]
    if exc.status_code is not None:
        lines.append(f"Statut API: {exc.status_code}")
    if exc.raw_message:
        lines.append(f"Detail backend: {exc.raw_message}")
    return "\n".join(lines)


def _render_result(*, state: PlaygroundState, controls, result: AnalyzeResult) -> None:
    normalized_decision = result.decision.strip().upper()
    controls.score_label.text = f"Score: {result.score}"
    controls.decision_badge.text = f"Decision: {normalized_decision}"
    _set_badge_color(controls.decision_badge, get_decision_color(normalized_decision))
    _set_element_visibility(controls.decision_badge, bool(normalized_decision))
    _render_covered_elements_table(
        ui_module=ui,
        container=controls.covered_elements_container,
        covered_elements=result.covered_elements,
        extractions=result.extractions,
    )
    _render_missing_elements_list(
        ui_module=ui,
        container=controls.missing_elements_container,
        elements=result.missing_elements,
    )
    controls.technical_details_label.text = _format_technical_details(result)
    controls.result_live_region.text = (
        f"Resultat d'analyse mis a jour: decision {normalized_decision}, score {result.score}."
    )


def _format_technical_details(result: AnalyzeResult) -> str:
    lines = [f"Profil utilise: {result.profile_used}"]
    if result.model_used:
        lines.append(f"Modele utilise: {result.model_used}")
    if result.latency_sec is not None:
        lines.append(f"Latence: {result.latency_sec:.2f} s")
    return "\n".join(lines)


def _apply_playground_example(
    *,
    state: PlaygroundState,
    controls,
    example: GoldenDatasetEntry,
) -> None:
    state.text = example.text
    state.selected_profile_id = example.profile_id
    _set_control_value(controls.textarea, example.text)
    _set_control_value(controls.profile_select, example.profile_id)
    _sync_inference_engine_for_profile(
        state=state,
        controls=controls,
        profile_to_inference_engine=state.profile_engine_map,
    )
    route_label = example.profile_id or "inconnu"
    _set_feedback_message(
        controls,
        f"Exemple charge ({example.decision_expected}): {example.id} | Profil preselectionne: {route_label}",
    )


def _build_golden_dataset_entry(
    payload: dict[str, object],
    *,
    line_number: int,
    path: Path,
) -> GoldenDatasetEntry:
    entry_id = _read_required_dataset_string(payload, key="id", line_number=line_number, path=path)
    profile_id = _read_required_dataset_string(
        payload,
        key="profile_id",
        line_number=line_number,
        path=path,
    )
    text = _read_required_dataset_string(payload, key="text", line_number=line_number, path=path)
    decision_expected = _read_required_dataset_string(
        payload,
        key="decision_expected",
        line_number=line_number,
        path=path,
    ).upper()
    if decision_expected not in DECISION_COLOR_MAP:
        raise ValueError(
            f"Decision attendue invalide a la ligne {line_number} dans {path}: {decision_expected}"
        )

    tags = _read_dataset_tags(payload, line_number=line_number, path=path)
    work_note = payload.get("work_note")
    if work_note is not None and not isinstance(work_note, str):
        raise ValueError(f"work_note invalide a la ligne {line_number} dans {path}")

    normalized_work_note = work_note.strip() if isinstance(work_note, str) else None
    reserved_keys = {"id", "profile_id", "text", "decision_expected", "tags", "work_note"}
    extra_fields = {key: value for key, value in payload.items() if key not in reserved_keys}

    return GoldenDatasetEntry(
        id=entry_id,
        profile_id=profile_id,
        text=text,
        decision_expected=decision_expected,
        tags=tags,
        work_note=normalized_work_note or None,
        extra_fields=extra_fields,
    )


def _read_required_dataset_string(
    payload: dict[str, object],
    *,
    key: str,
    line_number: int,
    path: Path,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Champ {key!r} invalide a la ligne {line_number} dans {path}")

    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"Champ {key!r} vide a la ligne {line_number} dans {path}")
    return normalized_value


def _read_dataset_tags(
    payload: dict[str, object],
    *,
    line_number: int,
    path: Path,
) -> tuple[str, ...]:
    raw_tags = payload.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError(f"Champ 'tags' invalide a la ligne {line_number} dans {path}")

    tags: list[str] = []
    for raw_tag in raw_tags:
        if not isinstance(raw_tag, str):
            raise ValueError(f"Tag invalide a la ligne {line_number} dans {path}")

        normalized_tag = raw_tag.strip()
        if normalized_tag and normalized_tag not in tags:
            tags.append(normalized_tag)
    return tuple(tags)


def _format_playground_example_decision(decision_expected: str) -> tuple[str, str]:
    normalized_decision = decision_expected.strip().upper()
    if normalized_decision == "PARTIEL":
        return "Partiel", "◐"
    if normalized_decision == "OK":
        return "OK", "•"
    if normalized_decision == "KO":
        return "KO", "×"
    return normalized_decision or "Exemple", "◦"


def _format_playground_example_label(example: GoldenDatasetEntry) -> str:
    preview = _build_playground_example_preview(example.text)
    return f"{example.id} - {preview}" if preview else example.id


def _build_playground_example_preview(text: str) -> str:
    preview = " ".join(text.split())
    if not preview:
        return ""

    for prefix in (
        "Objet : ",
        "Objet: ",
        "Demande d'achat : ",
        "Demande d'absence - ",
        "Demande de devis - ",
        "Demande d'evolution - ",
        "Fiche de validation qualite - ",
        "RAPPORT JOURNALIER - ",
        "Compte-rendu projet ",
        "Suivi eleve : ",
        "Bonjour, ",
        "Bonjour ",
    ):
        if preview.startswith(prefix):
            preview = preview[len(prefix) :].strip()
            break

    if ". " in preview:
        first_sentence = preview.split(". ", 1)[0].strip()
        if 12 <= len(first_sentence) <= 52:
            preview = first_sentence

    if len(preview) > 36:
        preview = f"{preview[:33].rstrip()}..."

    return preview


def _format_playground_example_link_class(decision_expected: str) -> str:
    normalized_decision = decision_expected.strip().upper()
    if normalized_decision == "OK":
        return "covex-example-link-ok"
    if normalized_decision == "PARTIEL":
        return "covex-example-link-partiel"
    return "covex-example-link-ko"


def _sort_playground_examples(
    examples: list[GoldenDatasetEntry],
) -> list[GoldenDatasetEntry]:
    decision_order = {"KO": 0, "PARTIEL": 1, "OK": 2}
    return sorted(
        examples,
        key=lambda example: (
            decision_order.get(example.decision_expected.strip().upper(), 99),
            len(" ".join(example.text.split())),
            example.id,
        ),
    )


def _set_badge_color(badge, color: str) -> None:
    if hasattr(badge, "set_color"):
        badge.set_color(color)
        return
    if hasattr(badge, "props"):
        badge.props(f"color={color}")
        return
    badge.color = color


def _normalize_optional_selection(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None

    normalized = raw_value.strip()
    return normalized or None


def _sync_inference_engine_for_profile(
    *,
    state: PlaygroundState,
    controls: PlaygroundControls | Any,
    profile_to_inference_engine: dict[str, str],
    inference_engine_details_map: dict[str, str] | None = None,
    default_inference_engine: str | None = None,
) -> None:
    selected_profile_id = _normalize_optional_selection(state.selected_profile_id)
    next_inference_engine = profile_to_inference_engine.get(selected_profile_id or "")
    state.selected_inference_engine = next_inference_engine
    _set_control_value(controls.inference_engine_select, next_inference_engine)
    if inference_engine_details_map is not None:
        _update_inference_engine_help(
            controls=controls,
            selected_inference_engine=next_inference_engine,
            inference_engine_details_map=inference_engine_details_map,
            default_inference_engine=default_inference_engine,
        )


def _set_control_value(control: Any, value: str | None) -> None:
    if hasattr(control, "set_value"):
        control.set_value(value)
    else:
        control.value = value
    if hasattr(control, "update"):
        control.update()


def _set_html_content(element: Any, content: str) -> None:
    if hasattr(element, "set_content"):
        element.set_content(content)
    elif hasattr(element, "content"):
        element.content = content
    else:
        element.text = content
    if hasattr(element, "update"):
        element.update()


def _render_covered_elements_table(
    *,
    ui_module: Any,
    container: Any,
    covered_elements: tuple[str, ...] | list[str],
    extractions: tuple[dict, ...] | list[dict[str, object]],
) -> None:
    container.clear()

    grouped_extractions = _group_extractions_by_criterion(extractions)
    rows: list[tuple[str, str]] = []

    for item in covered_elements:
        normalized_item = item.strip()
        if not normalized_item:
            continue
        extraction_texts = grouped_extractions.pop(normalized_item, [])
        rows.append((normalized_item, _format_extraction_texts(extraction_texts)))

    for criterion, extraction_texts in grouped_extractions.items():
        rows.append((criterion, _format_extraction_texts(extraction_texts)))

    with container:
        _render_section_header(
            ui_module=ui_module,
            title="Elements couverts et extraits",
            accent_class="text-positive",
            icon="checklist",
        )
        if not rows:
            ui_module.label("Aucun element couvert ou extrait retourne.").classes("text-grey-7")
            return

        with ui_module.column().classes("w-full gap-0 rounded-borders bg-grey-1 q-pa-sm"):
            _render_covered_elements_table_row(
                ui_module=ui_module,
                element_label="Element",
                extraction_label="Extraction",
                header=True,
            )
            for element_label, extraction_label in rows:
                _render_covered_elements_table_row(
                    ui_module=ui_module,
                    element_label=element_label,
                    extraction_label=extraction_label,
                )


def _render_missing_elements_list(
    *,
    ui_module: Any,
    container: Any,
    elements: tuple[str, ...] | list[str],
) -> None:
    container.clear()

    normalized_elements = [item.strip() for item in elements if item.strip()]
    with container:
        _render_section_header(
            ui_module=ui_module,
            title="Elements manquants",
            accent_class="text-negative",
            icon="warning",
        )
        if not normalized_elements:
            ui_module.label("Aucun element manquant retourne.").classes("text-grey-7")
            return

        with ui_module.column().classes("w-full gap-1 rounded-borders bg-grey-1 q-pa-sm"):
            for item in normalized_elements:
                with ui_module.row().classes("items-center gap-2"):
                    ui_module.icon("remove").classes("text-negative")
                    ui_module.label(item)


def _render_section_header(
    *,
    ui_module: Any,
    title: str,
    accent_class: str,
    icon: str,
) -> None:
    with ui_module.row().classes(
        "w-full items-center gap-2 rounded-borders bg-grey-2 q-px-sm q-py-xs"
    ):
        ui_module.icon(icon).classes(accent_class)
        ui_module.label(title).classes(f"text-subtitle2 {accent_class}")


def _group_extractions_by_criterion(
    extractions: tuple[dict, ...] | list[dict[str, object]],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for raw_extraction in extractions:
        if not isinstance(raw_extraction, dict):
            continue

        criterion = str(
            raw_extraction.get("criterion_id")
            or raw_extraction.get("class")
            or raw_extraction.get("text")
            or ""
        ).strip()
        if not criterion:
            continue

        text = str(raw_extraction.get("text") or "").strip()
        if criterion not in grouped:
            grouped[criterion] = []
        if text and text not in grouped[criterion]:
            grouped[criterion].append(text)
    return grouped


def _format_extraction_texts(extraction_texts: list[str]) -> str:
    if not extraction_texts:
        return "-"
    return " | ".join(f'"{text}"' for text in extraction_texts)


def _render_covered_elements_table_row(
    *,
    ui_module: Any,
    element_label: str,
    extraction_label: str,
    header: bool = False,
) -> None:
    row_classes = "w-full items-start no-wrap q-col-gutter-md q-py-sm"
    if header:
        row_classes = f"{row_classes} text-weight-medium text-grey-8 border-b"
    else:
        row_classes = f"{row_classes} border-b border-grey-3"

    with ui_module.row().classes(row_classes):
        ui_module.label(element_label).classes("w-1/3 text-weight-medium")
        ui_module.label(extraction_label).classes("w-2/3 whitespace-pre-wrap")


def _set_element_visibility(element: Any, visible: bool) -> None:
    if hasattr(element, "set_visibility"):
        element.set_visibility(visible)
    else:
        element.visible = visible
    if hasattr(element, "update"):
        element.update()


def _build_nav_row(ui_module: Any) -> None:
    """Affiche la barre de navigation commune aux pages du playground."""
    with ui_module.row().classes("w-full items-center justify-between gap-2 q-mb-sm"):
        ui_module.link("Playground", "/")
        ui_module.link("Golden dataset", "/golden-dataset")
        ui_module.link("Analysis profiles", "/analysis-profiles")


def load_analysis_profiles_from_config(
    *, config_dir: Path | None = None
) -> list[dict[str, object]]:
    """Charge et structure les profils d'analyse depuis le YAML de config."""
    payload = _load_yaml_config(ANALYSIS_PROFILES_FILE, config_dir=config_dir)
    if payload is None:
        return []
    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, dict):
        return []

    profiles: list[dict[str, object]] = []
    for profile_id, raw_profile in raw_profiles.items():
        if not isinstance(profile_id, str) or not isinstance(raw_profile, dict):
            continue
        profiles.append({"id": profile_id, **raw_profile})
    return profiles


def build_analysis_profiles_page() -> None:
    """
    Construit la page NiceGUI de visualisation des profils d'analyse (lecture seule).
    Affiche les criteres, poids, exemples d'extraction de chaque profil.
    """
    profiles = load_analysis_profiles_from_config()

    with ui.card().classes("w-full max-w-5xl mx-auto q-mt-lg"):
        _build_nav_row(ui)

        ui.label("Analysis profiles").classes("text-h5")
        ui.label(f"Fichier : {ANALYSIS_PROFILES_FILE}  •  {len(profiles)} profils").classes(
            "text-caption text-grey-7 q-mb-sm"
        )

        if not profiles:
            ui.label("Aucun profil charge depuis la configuration.").classes(
                "text-body1 text-grey-7"
            )
            return

        for profile in profiles:
            profile_id = str(profile.get("id", "")).strip()
            name = str(profile.get("name", profile_id)).strip()
            description = str(profile.get("description", "")).strip()
            engine_key = str(profile.get("inference_engine_key", "")).strip()
            coverage_items = profile.get("coverage_item")
            le_few_shot = profile.get("le_few_shot")

            with (
                ui.expansion(name, value=False)
                .props("icon=description header-class='rounded-borders bg-grey-2 q-pa-sm'")
                .classes("w-full q-mt-sm")
            ):
                with ui.column().classes("w-full gap-3 q-px-sm q-pb-sm"):
                    with ui.row().classes("w-full flex-wrap gap-4 items-start"):
                        with ui.column().classes("gap-1"):
                            ui.label("Identifiant").classes("text-caption text-grey-7")
                            ui.label(profile_id).classes("text-body2 text-weight-medium")
                        if description:
                            with ui.column().classes("gap-1 flex-1"):
                                ui.label("Description").classes("text-caption text-grey-7")
                                ui.label(description).classes("text-body2")
                        if engine_key:
                            with ui.column().classes("gap-1"):
                                ui.label("Moteur d'inference").classes("text-caption text-grey-7")
                                ui.badge(engine_key, color="primary").props("outline")

                    ui.separator()

                    # Criteres de couverture
                    if isinstance(coverage_items, list) and coverage_items:
                        with ui.column().classes("w-full gap-1"):
                            with ui.row().classes("items-center gap-2 q-mb-xs"):
                                ui.icon("checklist").classes("text-primary")
                                ui.label("Criteres de couverture").classes(
                                    "text-subtitle2 text-primary"
                                )

                            total_weight = sum(
                                float(item.get("weight", 0))
                                for item in coverage_items
                                if isinstance(item, dict)
                            )

                            with ui.column().classes(
                                "w-full gap-0 rounded-borders bg-grey-1 q-pa-sm"
                            ):
                                # En-tete tableau
                                with ui.row().classes(
                                    "w-full items-center q-py-xs text-weight-medium text-grey-8"
                                ):
                                    ui.label("Identifiant").classes("col-3 text-caption")
                                    ui.label("Poids").classes("col-1 text-caption")
                                    ui.label("Information attendue").classes("col-8 text-caption")

                                for item in coverage_items:
                                    if not isinstance(item, dict):
                                        continue
                                    item_id = str(item.get("id", "")).strip()
                                    weight = item.get("weight", 0)
                                    expected_info = str(item.get("expected_info", "")).strip()
                                    pct = (
                                        f"{float(weight) * 100:.0f}%"
                                        if isinstance(weight, (int, float))
                                        else str(weight)
                                    )
                                    with ui.row().classes(
                                        "w-full items-start q-py-xs border-t border-grey-3"
                                    ):
                                        ui.label(item_id).classes(
                                            "col-3 text-body2 text-weight-medium"
                                        )
                                        ui.badge(pct, color="blue-grey").props("outline").classes(
                                            "col-1"
                                        )
                                        ui.label(expected_info).classes(
                                            "col-8 text-body2 text-grey-8"
                                        )

                            if total_weight > 0:
                                ui.label(f"Total poids : {total_weight * 100:.0f}%").classes(
                                    "text-caption text-grey-7 q-mt-xs"
                                )

                    # Exemples de calibrage (few-shot)
                    if isinstance(le_few_shot, list) and le_few_shot:
                        with ui.column().classes("w-full gap-2 q-mt-xs"):
                            with ui.row().classes("items-center gap-2 q-mb-xs"):
                                ui.icon("model_training").classes("text-secondary")
                                ui.label("Exemples de calibrage").classes(
                                    "text-subtitle2 text-secondary"
                                )

                            for idx, example in enumerate(le_few_shot, start=1):
                                if not isinstance(example, dict):
                                    continue
                                example_text = str(example.get("text", "")).strip()
                                extractions = example.get("extractions")

                                with (
                                    ui.card()
                                    .classes("w-full q-pa-sm bg-grey-1 rounded-borders")
                                    .style("border-left: 3px solid #9c27b0")
                                ):
                                    with ui.column().classes("w-full gap-1"):
                                        ui.label(f"Exemple {idx}").classes(
                                            "text-caption text-grey-7"
                                        )
                                        ui.label(f'"{example_text}"').classes(
                                            "text-body2 text-italic text-grey-9"
                                        )

                                        if isinstance(extractions, list) and extractions:
                                            with ui.element("div").style(
                                                "display:grid;"
                                                "grid-template-columns:12rem 1fr;"
                                                "gap:0;"
                                                "margin-top:0.4rem;"
                                                "width:100%;"
                                            ):
                                                for extraction in extractions:
                                                    if not isinstance(extraction, dict):
                                                        continue
                                                    crit = str(
                                                        extraction.get("criterion_id", "")
                                                    ).strip()
                                                    ext_text = str(
                                                        extraction.get("extraction_text", "")
                                                    ).strip()
                                                    ui.label(crit).classes(
                                                        "text-caption text-weight-medium"
                                                        " text-primary q-py-xs"
                                                    ).style(
                                                        "border-top:1px solid #e0e0e0;"
                                                        "padding-right:0.5rem;"
                                                    )
                                                    ui.label(f'"{ext_text}"').classes(
                                                        "text-caption text-italic text-grey-8"
                                                        " q-py-xs"
                                                    ).style("border-top:1px solid #e0e0e0;")
                                        elif isinstance(extractions, list):
                                            ui.label("(aucune extraction attendue)").classes(
                                                "text-caption text-grey-6"
                                            )


def _load_yaml_config(filename: str, *, config_dir: Path | None = None) -> dict[str, object] | None:
    """Charge un YAML de configuration et retourne son dictionnaire racine, sinon None."""
    resolved_dir = config_dir or _resolve_default_config_dir()
    path = resolved_dir / filename
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError):
        return None
    return payload if isinstance(payload, dict) else None


def _resolve_default_config_dir() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / CONFIG_DIRECTORY
        if candidate.exists() and candidate.is_dir():
            return candidate
    return Path(CONFIG_DIRECTORY)


def _resolve_default_dataset_path() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / DATASETS_DIRECTORY / GOLDEN_DATASET_FILE
        if candidate.exists() and candidate.is_file():
            return candidate
    return Path(DATASETS_DIRECTORY) / GOLDEN_DATASET_FILE
