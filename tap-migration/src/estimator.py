from __future__ import annotations
import math
from dataclasses import dataclass

_AUTOMATED_FRAMEWORKS = {"pytest", "unittest"}
_CASES_PER_DAY = 200  # manual review throughput
_DATA_FORMAT_EFFORT: dict[str, float] = {
    "excel": 0.5,
    "database": 1.0,
    "db": 1.0,
}


@dataclass
class EffortResult:
    manual_cases: int
    effort_days: float
    summary: str


def estimate_effort(
    framework: str | None,
    test_case_count: int,
    data_format: str | None,
) -> EffortResult:
    """Estimate migration effort in person-days."""
    fw = (framework or "").lower()

    if fw in _AUTOMATED_FRAMEWORKS:
        manual_cases = 0
        case_days = 0.0
    else:
        manual_cases = test_case_count
        raw_days = test_case_count / _CASES_PER_DAY
        case_days = math.ceil(raw_days * 2) / 2  # round up to nearest 0.5

    fmt = (data_format or "").lower()
    data_days = _DATA_FORMAT_EFFORT.get(fmt, 0.0)

    effort_days = case_days + data_days

    if effort_days == 0.0:
        summary = "Fully automated — no manual work required"
    else:
        parts = []
        if manual_cases > 0:
            parts.append(f"{manual_cases} test cases need manual review")
        if data_days > 0:
            parts.append(f"test data format requires conversion")
        summary = f"{'; '.join(parts)} — estimated {effort_days:.1f} person-day{'s' if effort_days != 1.0 else ''}"

    return EffortResult(
        manual_cases=manual_cases,
        effort_days=effort_days,
        summary=summary,
    )
