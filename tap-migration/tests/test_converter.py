import pytest
import json
from pathlib import Path
from src.converter import convert_test_data_file, convert_test_case_file, ConversionError


def test_converts_csv_to_tap_payload(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,name,value\n1,foo,bar\n2,baz,qux\n")
    records = convert_test_data_file(csv_file)
    assert len(records) == 2
    assert records[0]["id"] == "1"
    assert records[0]["name"] == "foo"


def test_converts_json_to_tap_payload(tmp_path):
    json_file = tmp_path / "data.json"
    json_file.write_text(json.dumps([{"id": "1", "name": "alpha"}]))
    records = convert_test_data_file(json_file)
    assert len(records) == 1
    assert records[0]["name"] == "alpha"


def test_raises_on_unsupported_format(tmp_path):
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("hello")
    with pytest.raises(ConversionError, match="Unsupported"):
        convert_test_data_file(txt_file)


def test_converts_python_test_file_to_tap_cases(tmp_path):
    test_file = tmp_path / "test_login.py"
    test_file.write_text(
        "def test_valid_login(): pass\ndef test_invalid_password(): pass\n"
    )
    cases = convert_test_case_file(test_file)
    assert len(cases) == 2
    assert cases[0]["name"] == "test_valid_login"
    assert cases[0]["steps"] == []


def test_skips_non_test_functions(tmp_path):
    test_file = tmp_path / "test_utils.py"
    test_file.write_text("def helper(): pass\ndef test_real(): pass\n")
    cases = convert_test_case_file(test_file)
    assert len(cases) == 1
