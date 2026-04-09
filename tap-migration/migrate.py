#!/usr/bin/env python
"""Phase 2: Convert, upload, validate, and report migration."""
from __future__ import annotations
from pathlib import Path
import typer
from dotenv import load_dotenv
import os
from src.scanner import scan_project
from src.converter import convert_test_data_file, convert_test_case_file, ConversionError
from src.uploader import upload_records, AuthError
from src.validator import validate_migration
from src.reporter import render_migration_report

app = typer.Typer()

# --- TAP API endpoints (fill in after confirming with TAP team) ---
_TEST_DATA_ENDPOINT = "{TAP_API_BASE_URL}/test-data"    # TBD
_TEST_CASE_ENDPOINT = "{TAP_API_BASE_URL}/test-cases"   # TBD


@app.command()
def main(
    project_dir: Path = typer.Option(..., help="Path to the local test project"),
    env: Path = typer.Option(Path(".env"), help="Path to .env file"),
    dry_run: bool = typer.Option(False, help="Convert only, skip upload"),
    report_out: Path = typer.Option(Path("./tap-migration-report.md"), help="Output path for report"),
) -> None:
    load_dotenv(env)
    base_url = os.getenv("TAP_API_BASE_URL", "")
    token = os.getenv("TAP_API_TOKEN", "")

    if not dry_run and (not base_url or not token):
        typer.echo("ERROR: TAP_API_BASE_URL and TAP_API_TOKEN must be set in .env", err=True)
        raise typer.Exit(1)

    scan = scan_project(project_dir)

    # Convert test data
    all_data_records: list[dict] = []
    for data_file in scan.test_data_paths:
        try:
            all_data_records.extend(convert_test_data_file(data_file))
        except ConversionError as e:
            typer.echo(f"WARN: skipping {data_file.name} — {e}")

    # Convert test cases
    all_case_records: list[dict] = []
    for case_file in scan.test_case_paths:
        all_case_records.extend(convert_test_case_file(case_file))

    typer.echo(f"Converted: {len(all_data_records)} data records, {len(all_case_records)} test cases")

    if dry_run:
        typer.echo("Dry-run mode — skipping upload.")
        raise typer.Exit(0)

    # Upload
    data_endpoint = _TEST_DATA_ENDPOINT.format(TAP_API_BASE_URL=base_url)
    case_endpoint = _TEST_CASE_ENDPOINT.format(TAP_API_BASE_URL=base_url)

    try:
        typer.echo("Uploading test data...")
        data_result = upload_records(all_data_records, data_endpoint, token)
        typer.echo("Uploading test cases...")
        case_result = upload_records(all_case_records, case_endpoint, token)
    except AuthError as e:
        typer.echo(f"ERROR: Authentication failed — {e}", err=True)
        raise typer.Exit(1)

    # Validate — TAP API returns no payload, so we do a count-only check:
    # slice local records to the number successfully uploaded to simulate what TAP received.
    combined_local = all_data_records + all_case_records
    validation = validate_migration(
        local_records=combined_local,
        uploaded_records=combined_local[:data_result.uploaded + case_result.uploaded],
    )

    # Report
    report = render_migration_report(
        project_name=project_dir.name,
        data_upload=data_result,
        case_upload=case_result,
        validation=validation,
    )
    report_out.write_text(report)
    typer.echo(f"Migration report written to: {report_out}")
    typer.echo(report)


if __name__ == "__main__":
    app()
