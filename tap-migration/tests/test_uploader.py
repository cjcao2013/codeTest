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
