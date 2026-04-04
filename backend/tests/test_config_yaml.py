"""Verifie que les fichiers YAML de configuration CoVeX restent chargeables."""

from pathlib import Path
from inference import load_inference_engines_config
from analysis_profiles_config import load_analysis_profiles_config


def test_config_yaml_files_are_parseable() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    config_dir = repo_root / "config"
    load_inference_engines_config(config_dir=config_dir)
    load_analysis_profiles_config(config_dir=config_dir)


def test_inference_engines_yaml_is_schema_valid() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    config_dir = repo_root / "config"
    config = load_inference_engines_config(config_dir=config_dir)
    assert config.default_inference_engine_key in config.inference_engines


def test_analysis_profiles_yaml_is_schema_valid() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    config_dir = repo_root / "config"
    config = load_analysis_profiles_config(config_dir=config_dir)
    assert config.profiles
