"""
Charge, valide et expose les profils d'analyse configures dans `config/analysis_profiles.yaml`.

Usage:
- Module importe par `backend/src/main.py` pour enregistrer la route `GET /analysis-profiles`.
- Reutilise par `backend/src/analysis.py` et `tools/research/select_engines_by_cost_score.py` pour
  resoudre un `profile_id` et ses criteres.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from inference import BrainEnginesConfig

CONFIG_DIRECTORY = "config"
ANALYSIS_PROFILES_FILE = "analysis_profiles.yaml"


class AnalysisProfileCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1)
    expected_info: str = Field(min_length=1)
    weight: float = Field(gt=0.0, le=1.0)


class AnalysisProfileExtractionExampleItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    criterion_id: str = Field(min_length=1)
    extraction_text: str = Field(min_length=1)


class AnalysisProfileExtractionExample(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1)
    extractions: list[AnalysisProfileExtractionExampleItem] = Field(default_factory=list)


class AnalysisProfileDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    coverage_item: list[AnalysisProfileCriterion] = Field(min_length=1)
    le_few_shot: list[AnalysisProfileExtractionExample] = Field(default_factory=list)
    inference_engine_key: str | None = Field(default=None, min_length=1)


class AnalysisProfilesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    profiles: dict[str, AnalysisProfileDefinition]


class AnalysisProfilesConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class AnalysisProfileRuntime:
    profile_id: str
    prompt_text: str
    criterion_ids: list[str]
    criterion_weights: dict[str, float]
    le_few_shot: list[dict[str, object]]
    inference_engine_key: str | None


_cached_config: AnalysisProfilesConfig | None = None


def load_analysis_profiles_config(
    *, config_dir: Path | None = None, inference_engines_config: BrainEnginesConfig | None = None
) -> AnalysisProfilesConfig:
    global _cached_config
    if _cached_config is not None and config_dir is None:
        return _cached_config

    resolved_dir = config_dir or _resolve_default_config_dir()
    path = resolved_dir / ANALYSIS_PROFILES_FILE

    if not path.exists():
        raise AnalysisProfilesConfigurationError(f"Missing required configuration file: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            payload = yaml.safe_load(file)
        config = AnalysisProfilesConfig.model_validate(payload)
        if config_dir is None:
            _cached_config = config
        return config
    except Exception as exc:
        raise AnalysisProfilesConfigurationError(f"Invalid config: {exc}") from exc


def load_runtime_analysis_profiles(
    *, config_dir: Path | None = None, inference_engines_config: BrainEnginesConfig | None = None
) -> dict[str, AnalysisProfileRuntime]:
    profiles_config = load_analysis_profiles_config(
        config_dir=config_dir, inference_engines_config=inference_engines_config
    )
    runtime_profiles = {}

    for profile_id, definition in profiles_config.profiles.items():
        coverage_item_lines = [
            f"- {c.id} (poids: {c.weight}): {c.expected_info}" for c in definition.coverage_item
        ]
        prompt = (
            f"Profil: {definition.name}\nContexte: {definition.description}\n\nObjectif principal: determiner si chaque critere est present.\n\n"
            + "\n".join(coverage_item_lines)
        )

        examples = []
        for ex in definition.le_few_shot:
            examples.append(
                {
                    "text": ex.text,
                    "extractions": [
                        {"criterion_id": e.criterion_id, "extraction_text": e.extraction_text}
                        for e in ex.extractions
                    ],
                }
            )

        runtime_profiles[profile_id] = AnalysisProfileRuntime(
            profile_id=profile_id,
            prompt_text=prompt,
            criterion_ids=[c.id for c in definition.coverage_item],
            criterion_weights={c.id: c.weight for c in definition.coverage_item},
            le_few_shot=examples,
            inference_engine_key=definition.inference_engine_key,
        )
    return runtime_profiles


def _resolve_default_config_dir() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / CONFIG_DIRECTORY
        if candidate.exists() and candidate.is_dir():
            return candidate
    return Path(CONFIG_DIRECTORY)
