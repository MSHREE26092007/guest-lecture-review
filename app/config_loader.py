"""YAML config loading with caching. All checklist/spec/rubric files live in config/."""

from functools import lru_cache
from pathlib import Path

import yaml

from app.config import get_settings


@lru_cache(maxsize=None)
def load_config(name: str) -> dict:
    """Load config/<name>.yaml and return it as a dict."""
    path: Path = get_settings().config_dir / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_required_fields() -> dict:
    return load_config("required_fields")


def load_formatting_spec() -> dict:
    return load_config("formatting_spec")


def load_policy_checklist() -> dict:
    return load_config("policy_checklist")


def load_scoring_rubric() -> dict:
    return load_config("scoring_rubric")