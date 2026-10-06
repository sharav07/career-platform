"""Load and validate the checked-in resume seed."""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path

from pydantic import ValidationError

from app.models import ResumeSeed


def load_seed(path: str | Path) -> ResumeSeed:
    """Parse and validate a JSON resume seed from ``path``."""
    seed_path = Path(path)
    try:
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
    except JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in seed file {seed_path}: {error.msg}") from error
    except OSError as error:
        raise ValueError(f"Unable to read seed file {seed_path}: {error}") from error

    try:
        return ResumeSeed.model_validate(payload)
    except ValidationError as error:
        raise ValueError(f"Invalid resume seed {seed_path}: {error}") from error
