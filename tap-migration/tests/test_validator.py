import pytest
from src.validator import validate_migration, ValidationResult


def test_passes_when_counts_match():
    local = [{"id": str(i), "name": f"item{i}", "data": {"v": i}} for i in range(10)]
    uploaded = [{"id": str(i), "name": f"item{i}", "data": {"v": i}} for i in range(10)]
    result = validate_migration(local_records=local, uploaded_records=uploaded)
    assert result.count_match is True
    assert result.sample_failures == []


def test_fails_when_counts_differ():
    local = [{"id": "1", "name": "a", "data": {}}] * 5
    uploaded = [{"id": "1", "name": "a", "data": {}}] * 3
    result = validate_migration(local_records=local, uploaded_records=uploaded)
    assert result.count_match is False


def test_detects_name_mismatch_in_sample():
    local = [{"id": str(i), "name": f"item{i}", "data": {"v": i}} for i in range(20)]
    uploaded = [{"id": str(i), "name": f"WRONG{i}", "data": {"v": i}} for i in range(20)]
    result = validate_migration(local_records=local, uploaded_records=uploaded, seed=42)
    assert len(result.sample_failures) > 0


def test_sample_size_minimum_five():
    local = [{"id": str(i), "name": f"x{i}", "data": {}} for i in range(3)]
    uploaded = local[:]
    result = validate_migration(local_records=local, uploaded_records=uploaded)
    # With fewer than 5 records, all are sampled
    assert result.sample_size == 3


def test_sample_size_ten_percent_of_large_set():
    local = [{"id": str(i), "name": f"x{i}", "data": {}} for i in range(100)]
    uploaded = local[:]
    result = validate_migration(local_records=local, uploaded_records=uploaded)
    assert result.sample_size == 10
