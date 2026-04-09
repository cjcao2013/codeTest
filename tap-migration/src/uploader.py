from __future__ import annotations
import time
from dataclasses import dataclass, field
import httpx


class AuthError(Exception):
    pass


@dataclass
class UploadResult:
    uploaded: int = 0
    failed: int = 0
    failures: list[dict] = field(default_factory=list)


_MAX_RETRIES = 3
_RETRY_BASE_SECONDS = 1.0


def upload_records(
    records: list[dict],
    endpoint: str,
    token: str,
) -> UploadResult:
    """Upload records to a TAP API endpoint. Continue-on-error per record; abort on auth failure."""
    result = UploadResult()
    with httpx.Client(timeout=30) as client:
        for record in records:
            _upload_one(client, record, endpoint, token, result)
    return result


def _upload_one(
    client: httpx.Client,
    record: dict,
    endpoint: str,
    token: str,
    result: UploadResult,
) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    last_error: str = ""
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.post(endpoint, json=record, headers=headers)
            if response.status_code in (401, 403):
                raise AuthError(f"Auth failed: {response.status_code}")
            if response.is_success:
                result.uploaded += 1
                return
            # Non-auth HTTP error: don't retry, fail immediately
            last_error = f"HTTP {response.status_code}"
            break  # Don't retry HTTP errors
        except AuthError:
            raise
        except Exception as exc:
            # Network/timeout errors: retry with backoff
            last_error = str(exc)
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_BASE_SECONDS * (2 ** attempt))

    result.failed += 1
    result.failures.append({**record, "_error": last_error})
