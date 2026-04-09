from __future__ import annotations
from pathlib import Path


class ValidationError(ValueError):
    pass


def validate_path(
    value: str | None,
    *,
    must_exist: bool = False,
    must_be_dir: bool = False,
) -> Path | None:
    if value is None:
        return None
    if ".." in Path(value).parts:
        raise ValidationError(f"Path traversal not allowed: {value!r}")
    resolved = Path(value).resolve()
    if must_exist and not resolved.exists():
        raise ValidationError(f"Path does not exist: {resolved}")
    if must_be_dir and resolved.exists() and not resolved.is_dir():
        raise ValidationError(f"Path is not a directory: {resolved}")
    return resolved
