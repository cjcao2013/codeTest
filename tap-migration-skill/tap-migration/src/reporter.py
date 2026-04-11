from __future__ import annotations
from datetime import date
from enum import Enum
from src.uploader import UploadResult
from src.validator import ValidationResult


class DimensionStatus(Enum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"


_STATUS_ICON = {
    DimensionStatus.OK: "✅",
    DimensionStatus.WARN: "⚠️",
    DimensionStatus.ERROR: "❌",
}


def render_feasibility_report(
    project_name: str,
    dimensions: dict[str, DimensionStatus],
    risk_items: list[str],
    pending_items: list[str],
    effort_summary: str = "",
) -> str:
    has_error = any(s == DimensionStatus.ERROR for s in dimensions.values())
    warn_count = sum(1 for s in dimensions.values() if s == DimensionStatus.WARN)

    if has_error:
        complexity = "🔴 High"
        recommendation = "**No-go** — resolve blockers before proceeding"
    elif warn_count >= 1:
        complexity = "🟡 Medium"
        recommendation = "**Pending** — resolve ⚠️ items before starting migration"
    else:
        complexity = "🟢 Low"
        recommendation = "**Go** — all dimensions clear, migration can start"

    dim_rows = "\n".join(
        f"| {name} | {_STATUS_ICON[status]} | |"
        for name, status in dimensions.items()
    )
    risks = "\n".join(f"- {r}" for r in risk_items) or "- None identified"
    pending = "\n".join(f"- [ ] {p}" for p in pending_items) or "- None"
    effort_summary = effort_summary or "Not calculated"

    return f"""# TAP Migration Feasibility Report
Project: {project_name} | Date: {date.today()}

## Complexity Score: {complexity}

| Dimension | Status | Notes |
|-----------|--------|-------|
{dim_rows}

## Risk Items
{risks}

## Effort Estimate
{effort_summary}

## Recommendation
{recommendation}

## Pending (confirm with TAP team)
{pending}
"""


def render_migration_report(
    project_name: str,
    data_upload: UploadResult,
    case_upload: UploadResult,
    validation: ValidationResult,
) -> str:
    # Note: single validation result used for both rows (TAP returns no per-type payload)
    validation_icon = "✅" if validation.count_match and not validation.sample_failures else "⚠️"

    failures = []
    for f in data_upload.failures + case_upload.failures:
        record_id = f.get("id", "unknown")
        error = f.get("_error", "unknown error")
        failures.append(f"- `{record_id}`: {error}")
    failures_text = "\n".join(failures) or "- None"

    return f"""# TAP Migration Report
Project: {project_name} | Date: {date.today()}

## Summary
| Type | Local Count | Uploaded | Failed | Validation |
|------|------------|---------|--------|------------|
| Test data | {data_upload.uploaded + data_upload.failed} | {data_upload.uploaded} | {data_upload.failed} | {validation_icon} |
| Test cases | {case_upload.uploaded + case_upload.failed} | {case_upload.uploaded} | {case_upload.failed} | {validation_icon} |

## Failure Details
{failures_text}

## Next Steps
- [ ] Handle failed items manually
- [ ] Notify TAP team for acceptance
- [ ] Keep local backup until acceptance complete
"""
