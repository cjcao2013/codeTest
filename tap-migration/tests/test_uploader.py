import pytest
import respx
import httpx
from src.uploader import upload_records, UploadResult, AuthError


BASE_URL = "https://tap.test/api"
TOKEN = "test-token"


@respx.mock
def test_uploads_records_successfully():
    respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(200))
    result = upload_records(
        records=[{"id": "1", "name": "a", "data": {}}],
        endpoint=f"{BASE_URL}/test-data",
        token=TOKEN,
    )
    assert result.uploaded == 1
    assert result.failed == 0


@respx.mock
def test_continues_on_single_record_failure():
    route = respx.post(f"{BASE_URL}/test-data")
    route.side_effect = [
        httpx.Response(500),
        httpx.Response(200),
    ]
    result = upload_records(
        records=[{"id": "1", "name": "a", "data": {}}, {"id": "2", "name": "b", "data": {}}],
        endpoint=f"{BASE_URL}/test-data",
        token=TOKEN,
    )
    assert result.uploaded == 1
    assert result.failed == 1
    assert result.failures[0]["id"] == "1"


@respx.mock
def test_aborts_on_auth_failure():
    respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(401))
    with pytest.raises(AuthError):
        upload_records(
            records=[{"id": "1", "name": "a", "data": {}}],
            endpoint=f"{BASE_URL}/test-data",
            token=TOKEN,
        )


@respx.mock
def test_returns_empty_result_for_no_records():
    result = upload_records(records=[], endpoint=f"{BASE_URL}/test-data", token=TOKEN)
    assert result.uploaded == 0
    assert result.failed == 0


@respx.mock
def test_on_progress_called_for_each_record():
    respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(200))
    calls: list[tuple[int, int, dict]] = []
    records = [
        {"id": "1", "name": "a", "data": {}},
        {"id": "2", "name": "b", "data": {}},
        {"id": "3", "name": "c", "data": {}},
    ]
    upload_records(
        records=records,
        endpoint=f"{BASE_URL}/test-data",
        token=TOKEN,
        on_progress=lambda current, total, record: calls.append((current, total, record)),
    )
    assert len(calls) == 3
    assert calls[0] == (1, 3, records[0])
    assert calls[1] == (2, 3, records[1])
    assert calls[2] == (3, 3, records[2])


@respx.mock
def test_on_progress_called_even_on_failure():
    respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(500))
    calls: list[int] = []
    upload_records(
        records=[{"id": "1", "name": "a", "data": {}}],
        endpoint=f"{BASE_URL}/test-data",
        token=TOKEN,
        on_progress=lambda current, total, record: calls.append(current),
    )
    assert calls == [1]


def test_upload_delay_respected(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr("src.uploader.time.sleep", lambda s: sleep_calls.append(s))
    with respx.mock:
        respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(200))
        upload_records(
            records=[{"id": "1", "name": "a", "data": {}}, {"id": "2", "name": "b", "data": {}}],
            endpoint=f"{BASE_URL}/test-data",
            token=TOKEN,
            upload_delay=0.5,
        )
    assert sleep_calls == [0.5, 0.5]


def test_no_delay_by_default(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr("src.uploader.time.sleep", lambda s: sleep_calls.append(s))
    with respx.mock:
        respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(200))
        upload_records(
            records=[{"id": "1", "name": "a", "data": {}}],
            endpoint=f"{BASE_URL}/test-data",
            token=TOKEN,
        )
    assert 0.5 not in sleep_calls
