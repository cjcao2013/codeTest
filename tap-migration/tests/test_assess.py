from assess import _parse_volume_threshold, _volume_status
from src.reporter import DimensionStatus


def test_parse_volume_threshold_default():
    small, medium = _parse_volume_threshold("small:500,medium:5000")
    assert small == 500
    assert medium == 5000


def test_parse_volume_threshold_custom():
    small, medium = _parse_volume_threshold("small:100,medium:1000")
    assert small == 100
    assert medium == 1000


def test_volume_status_small():
    assert _volume_status(100, 500, 5000) == DimensionStatus.OK


def test_volume_status_medium():
    assert _volume_status(1000, 500, 5000) == DimensionStatus.WARN


def test_volume_status_large():
    assert _volume_status(10000, 500, 5000) == DimensionStatus.ERROR
