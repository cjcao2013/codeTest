#!/usr/bin/env python
"""Phase 1: Scan project, prompt for gaps, output feasibility report."""
from __future__ import annotations
from pathlib import Path
import typer
from src.scanner import scan_project
from src.reporter import render_feasibility_report, DimensionStatus
from src.estimator import estimate_effort

app = typer.Typer()


def _parse_volume_threshold(value: str) -> tuple[int, int]:
    try:
        parts = dict(kv.split(":") for kv in value.split(","))
        return int(parts["small"]), int(parts["medium"])
    except Exception:
        raise typer.BadParameter("Expected format: small:N,medium:N")


def _volume_status(count: int, small: int, medium: int) -> DimensionStatus:
    if count <= small:
        return DimensionStatus.OK
    if count <= medium:
        return DimensionStatus.WARN
    return DimensionStatus.ERROR


@app.command()
def main(
    project_dir: Path = typer.Option(..., help="Path to the local test project"),
    report_out: Path = typer.Option(Path("./tap-assessment-report.md"), help="Output path for report"),
    volume_threshold: str = typer.Option("small:500,medium:5000", help="Volume thresholds as small:N,medium:N"),
) -> None:
    small_threshold, medium_threshold = _parse_volume_threshold(volume_threshold)
    scan = scan_project(project_dir)

    # Framework
    framework = scan.test_framework
    if not framework:
        framework = typer.prompt("Test framework not detected. Which framework do you use? (pytest/unittest/other)")

    # Dep management
    dep_mgmt = scan.dep_management
    if not dep_mgmt:
        dep_mgmt = typer.prompt("Dependency management not detected. (requirements.txt/pyproject.toml/other)")

    # Test data format
    data_format = scan.test_data_format
    if not data_format:
        data_format = typer.prompt(
            "No test data files detected in project dir.\n"
            "Where is your test data? (local-files/database/external-tool/none)"
        )

    # Volume status
    vol_status = _volume_status(scan.test_data_count, small_threshold, medium_threshold)

    # Framework status
    supported_frameworks = {"pytest", "unittest"}
    warn_frameworks = {"robot_framework", "cucumber"}
    if framework and framework.lower() in supported_frameworks:
        framework_status = DimensionStatus.OK
    elif framework and framework.lower() in warn_frameworks:
        framework_status = DimensionStatus.WARN
    else:
        framework_status = DimensionStatus.ERROR

    # Data format status
    supported_formats = {"csv", "json", "yaml", "yml"}
    if data_format and data_format.lower() in supported_formats:
        data_fmt_status = DimensionStatus.OK
    elif data_format in ("none", ""):
        data_fmt_status = DimensionStatus.WARN
    else:
        data_fmt_status = DimensionStatus.WARN

    case_fmt_status = DimensionStatus.OK if scan.test_case_count > 0 else DimensionStatus.WARN

    dimensions = {
        "Test framework supported by TAP": framework_status,
        "Test data format readable by TAP": data_fmt_status,
        "Test data volume manageable": vol_status,
        "Test cases in migratable format": case_fmt_status,
    }

    risks = []
    if framework_status == DimensionStatus.WARN:
        risks.append(f"Framework '{framework}' detected — migration tooling in development, confirm with TAP team")
    if framework_status == DimensionStatus.ERROR:
        risks.append(f"Framework '{framework}' not recognised — confirm TAP support before proceeding")
    if vol_status == DimensionStatus.ERROR:
        risks.append(f"Large data volume ({scan.test_data_count} records) — plan for batched upload")
    if data_fmt_status == DimensionStatus.WARN:
        risks.append(f"Test data format '{data_format}' requires TAP team confirmation")

    pending = []
    if framework_status != DimensionStatus.OK:
        pending.append(f"Confirm TAP support for '{framework}' framework with TAP team")
    if data_fmt_status == DimensionStatus.WARN:
        pending.append("Confirm supported test data formats with TAP team")

    effort = estimate_effort(
        framework=framework,
        test_case_count=scan.test_case_count,
        data_format=data_format,
    )

    report = render_feasibility_report(
        project_name=project_dir.name,
        dimensions=dimensions,
        risk_items=risks,
        pending_items=pending,
        effort_summary=effort.summary,
    )

    report_out.write_text(report)
    typer.echo(f"Feasibility report written to: {report_out}")
    typer.echo(report)


if __name__ == "__main__":
    app()
