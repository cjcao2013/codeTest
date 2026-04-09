from src.reporter import render_feasibility_report, render_migration_report, DimensionStatus


def test_feasibility_report_contains_project_name():
    report = render_feasibility_report(
        project_name="my-tests",
        dimensions={
            "Test data format": DimensionStatus.OK,
            "Test case format": DimensionStatus.OK,
            "Data volume": DimensionStatus.WARN,
            "Project structure": DimensionStatus.OK,
        },
        risk_items=[],
        pending_items=[],
    )
    assert "my-tests" in report
    assert "🟡" in report  # Medium complexity due to one WARN


def test_feasibility_report_nogo_on_error():
    report = render_feasibility_report(
        project_name="x",
        dimensions={"Test data format": DimensionStatus.ERROR},
        risk_items=["Format not supported"],
        pending_items=[],
    )
    assert "Not recommended" in report


def test_migration_report_contains_summary():
    from src.uploader import UploadResult
    from src.validator import ValidationResult

    data_upload = UploadResult(uploaded=10, failed=0)
    case_upload = UploadResult(uploaded=5, failed=1, failures=[{"id": "tc1", "_error": "500"}])
    validation = ValidationResult(
        count_match=True, local_count=15, uploaded_count=14,
        sample_size=5, sample_failures=[]
    )

    report = render_migration_report(
        project_name="my-tests",
        data_upload=data_upload,
        case_upload=case_upload,
        validation=validation,
    )
    assert "10" in report
    assert "tc1" in report
    assert "500" in report
