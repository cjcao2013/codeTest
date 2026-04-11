from src.estimator import estimate_effort, EffortResult


def test_pytest_csv_fully_automated():
    result = estimate_effort(framework="pytest", test_case_count=42, data_format="csv")
    assert result.manual_cases == 0
    assert result.effort_days == 0.0
    assert result.summary == "Fully automated — no manual work required"


def test_unittest_json_fully_automated():
    result = estimate_effort(framework="unittest", test_case_count=10, data_format="json")
    assert result.manual_cases == 0
    assert result.effort_days == 0.0


def test_robot_framework_all_manual():
    result = estimate_effort(framework="robot_framework", test_case_count=100, data_format="csv")
    assert result.manual_cases == 100
    assert result.effort_days > 0


def test_cucumber_all_manual():
    result = estimate_effort(framework="cucumber", test_case_count=50, data_format="json")
    assert result.manual_cases == 50
    assert result.effort_days > 0


def test_unknown_framework_all_manual():
    result = estimate_effort(framework=None, test_case_count=30, data_format="csv")
    assert result.manual_cases == 30


def test_excel_data_adds_effort():
    auto = estimate_effort(framework="pytest", test_case_count=10, data_format="csv")
    excel = estimate_effort(framework="pytest", test_case_count=10, data_format="excel")
    assert excel.effort_days > auto.effort_days


def test_effort_days_rounded_to_half():
    result = estimate_effort(framework="robot_framework", test_case_count=50, data_format="csv")
    # 50 cases / 200 per day = 0.25 → rounds to 0.5
    assert result.effort_days == 0.5


def test_large_case_count():
    result = estimate_effort(framework="robot_framework", test_case_count=400, data_format="csv")
    assert result.effort_days == 2.0


def test_summary_includes_case_count_when_manual():
    result = estimate_effort(framework="cucumber", test_case_count=80, data_format="csv")
    assert "80" in result.summary
    assert "manual" in result.summary.lower()
