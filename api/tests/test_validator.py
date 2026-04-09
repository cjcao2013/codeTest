import pytest
from pathlib import Path
from services.validator import validate_path, ValidationError


def test_valid_existing_dir(tmp_path):
    result = validate_path(str(tmp_path), must_exist=True, must_be_dir=True)
    assert result == tmp_path.resolve()


def test_rejects_traversal():
    with pytest.raises(ValidationError, match="traversal"):
        validate_path("../../etc/passwd")


def test_rejects_missing_when_must_exist(tmp_path):
    with pytest.raises(ValidationError, match="does not exist"):
        validate_path(str(tmp_path / "missing"), must_exist=True)


def test_rejects_file_when_must_be_dir(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("x")
    with pytest.raises(ValidationError, match="not a directory"):
        validate_path(str(f), must_be_dir=True)


def test_optional_path_none_returns_none():
    assert validate_path(None) is None
