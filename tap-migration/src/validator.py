from __future__ import annotations
import random
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    count_match: bool
    local_count: int
    uploaded_count: int
    sample_size: int
    sample_failures: list[dict] = field(default_factory=list)


def validate_migration(
    local_records: list[dict],
    uploaded_records: list[dict],
    seed: int | None = None,
) -> ValidationResult:
    local_count = len(local_records)
    uploaded_count = len(uploaded_records)
    count_match = local_count == uploaded_count

    uploaded_by_id = {str(r.get("id", "")): r for r in uploaded_records}

    sample_size = max(5, int(local_count * 0.10)) if local_count >= 5 else local_count
    sample_size = min(sample_size, local_count)

    rng = random.Random(seed)
    sample = rng.sample(local_records, sample_size) if local_count > sample_size else local_records[:]

    failures = []
    for local in sample:
        record_id = str(local.get("id", ""))
        remote = uploaded_by_id.get(record_id)
        if remote is None:
            failures.append({"id": record_id, "reason": "not found in TAP"})
            continue
        if local.get("name") != remote.get("name"):
            failures.append({
                "id": record_id,
                "reason": f"name mismatch: local={local.get('name')!r} tap={remote.get('name')!r}",
            })

    return ValidationResult(
        count_match=count_match,
        local_count=local_count,
        uploaded_count=uploaded_count,
        sample_size=sample_size,
        sample_failures=failures,
    )
