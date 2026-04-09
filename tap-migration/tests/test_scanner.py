import pytest
from pathlib import Path
from src.scanner import scan_project, ScanResult


def test_detects_pytest_from_ini(tmp_path):
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    result = scan_project(tmp_path)
    assert result.test_framework == "pytest"


def test_detects_pytest_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    result = scan_project(tmp_path)
    assert result.test_framework == "pytest"


def test_detects_unittest_from_imports(tmp_path):
    test_file = tmp_path / "test_foo.py"
    test_file.write_text("import unittest\nclass T(unittest.TestCase): pass\n")
    result = scan_project(tmp_path)
    assert result.test_framework == "unittest"


def test_framework_unknown_when_no_signals(tmp_path):
    result = scan_project(tmp_path)
    assert result.test_framework is None


def test_detects_pyproject_dependency_management(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    result = scan_project(tmp_path)
    assert result.dep_management == "pyproject.toml"


def test_detects_requirements_txt(tmp_path):
    (tmp_path / "requirements.txt").write_text("pytest\n")
    result = scan_project(tmp_path)
    assert result.dep_management == "requirements.txt"


def test_counts_csv_test_data_files(tmp_path):
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    (data_dir / "a.csv").write_text("id,name\n1,foo\n")
    (data_dir / "b.csv").write_text("id,name\n2,bar\n")
    result = scan_project(tmp_path)
    assert result.test_data_format == "csv"
    assert result.test_data_count == 2


def test_counts_test_functions(tmp_path):
    (tmp_path / "test_foo.py").write_text(
        "def test_a(): pass\ndef test_b(): pass\n"
    )
    result = scan_project(tmp_path)
    assert result.test_case_count == 2


def test_unknown_test_data_when_empty(tmp_path):
    result = scan_project(tmp_path)
    assert result.test_data_format is None
    assert result.test_data_count == 0


def test_test_data_paths_populated(tmp_path):
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    csv_file = data_dir / "records.csv"
    csv_file.write_text("id,name\n1,foo\n")
    result = scan_project(tmp_path)
    assert csv_file in result.test_data_paths


def test_test_case_paths_populated(tmp_path):
    test_file = tmp_path / "test_login.py"
    test_file.write_text("def test_valid(): pass\n")
    result = scan_project(tmp_path)
    assert test_file in result.test_case_paths


def test_detects_nested_test_data(tmp_path):
    nested = tmp_path / "data" / "sub"
    nested.mkdir(parents=True)
    (nested / "nested.csv").write_text("id,name\n1,x\n")
    result = scan_project(tmp_path)
    assert result.test_data_count >= 1
