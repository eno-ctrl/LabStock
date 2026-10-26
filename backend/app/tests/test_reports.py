from fastapi.testclient import TestClient

from backend.app.services.report_service import sanitize_csv_cell


def test_csv_formula_injection_sanitization():
    # Dangerous values that could trigger DDE/command execution in Excel/LibreOffice Calc
    dangerous_inputs = [
        "=cmd|' /C calc'!A0",
        "+1+2",
        "-5+10",
        "@SUM(A1:A10)",
        "\tmalicious_tab",
        "\rmalicious_cr",
    ]
    for val in dangerous_inputs:
        sanitized = sanitize_csv_cell(val)
        assert sanitized.startswith("'"), f"Failed to sanitize: {val}"

    # Normal strings should not be prefixed
    assert sanitize_csv_cell("Standard SKU-101") == "Standard SKU-101"
    assert sanitize_csv_cell(123) == "123"
    assert sanitize_csv_cell(None) == ""


def test_reports_endpoints_json_and_csv(client: TestClient, viewer_headers: dict):
    # JSON stock report
    resp = client.get("/api/v1/reports/stock?format=json", headers=viewer_headers)
    assert resp.status_code == 200
    assert "data" in resp.json()

    # CSV stock report
    csv_resp = client.get("/api/v1/reports/stock?format=csv", headers=viewer_headers)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "attachment; filename=" in csv_resp.headers["content-disposition"]
