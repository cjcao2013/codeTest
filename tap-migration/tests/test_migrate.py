import pytest
import respx
import httpx
from pathlib import Path
from typer.testing import CliRunner
from migrate import app

runner = CliRunner()


def test_dry_run_skips_upload(tmp_path):
    (tmp_path / "test_foo.py").write_text("def test_a(): pass\n")
    result = runner.invoke(app, ["--project-dir", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "Dry-run" in result.output


def test_aborts_without_env_credentials(tmp_path):
    result = runner.invoke(app, ["--project-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "TAP_API_BASE_URL" in result.output or "TAP_API_TOKEN" in result.output


@respx.mock
def test_full_run_writes_report(tmp_path):
    (tmp_path / "test_foo.py").write_text("def test_a(): pass\n")
    env_file = tmp_path / ".env"
    env_file.write_text(
        "TAP_API_BASE_URL=https://tap.test/api\nTAP_API_TOKEN=tok\nTAP_PROJECT_ID=p1\n"
    )
    respx.post("https://tap.test/api/test-cases").mock(return_value=httpx.Response(200))
    respx.post("https://tap.test/api/test-data").mock(return_value=httpx.Response(200))

    report_path = tmp_path / "report.md"
    result = runner.invoke(app, [
        "--project-dir", str(tmp_path),
        "--env", str(env_file),
        "--report-out", str(report_path),
    ])
    assert result.exit_code == 0
    assert report_path.exists()


def test_upload_delay_flag_accepted(tmp_path):
    """--upload-delay 0.0 is accepted without error (dry-run so no actual upload)."""
    from typer.testing import CliRunner
    from migrate import app
    cli = CliRunner()

    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\nversion='0.1.0'\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_foo.py").write_text("def test_a(): pass\n")
    env_file = tmp_path / ".env"
    env_file.write_text("TAP_API_BASE_URL=http://localhost:9999\nTAP_API_TOKEN=tok\n")

    result = cli.invoke(app, [
        "--project-dir", str(tmp_path),
        "--env", str(env_file),
        "--dry-run",
        "--upload-delay", "0.0",
    ])
    assert result.exit_code == 0


def test_upload_delay_forwarded_to_upload_records(tmp_path):
    """upload_delay is passed as keyword arg to both upload_records calls."""
    from typer.testing import CliRunner
    from migrate import app
    from unittest.mock import patch, MagicMock
    cli = CliRunner()

    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\nversion='0.1.0'\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_foo.py").write_text("def test_alpha(): pass\ndef test_beta(): pass\n")
    env_file = tmp_path / ".env"
    env_file.write_text("TAP_API_BASE_URL=http://mock.test\nTAP_API_TOKEN=tok\n")

    with patch("migrate.upload_records") as mock_upload:
        mock_upload.return_value = MagicMock(uploaded=2, failed=0, failures=[])
        cli.invoke(app, [
            "--project-dir", str(tmp_path),
            "--env", str(env_file),
            "--upload-delay", "0.3",
        ])

    assert mock_upload.call_count == 2
    for call in mock_upload.call_args_list:
        assert call.kwargs.get("upload_delay") == 0.3
