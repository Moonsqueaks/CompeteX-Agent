from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import MarkdownReport, ReportData, TaskStatus, WordReport
from app.services import (
    MARKDOWN_REPORT_ARTIFACT_TYPE,
    REPORT_ARTIFACT_TYPE,
    WORD_REPORT_ARTIFACT_TYPE,
)
from app.storage import ArtifactRepository, TaskRepository


def _client(tmp_path: Path) -> tuple[TestClient, object]:
    database_url = f"sqlite:///{(tmp_path / 'reports_api.db').as_posix()}"
    api_app = create_app(database_url=database_url)
    api_app.state.report_output_dir = tmp_path / "reports"
    return TestClient(api_app), api_app


def _create_task(client: TestClient) -> str:
    response = client.post(
        "/tasks",
        json={
            "target_product_name": "报告接口目标",
            "target_product_url": "https://example.com/report",
            "category": "smart_pet_hardware",
            "subcategory": "automatic_litter_box",
            "data_source_mode": "demo_snapshot",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["task_id"]


def _mark_completed(api_app: object, task_id: str) -> None:
    session = api_app.state.session_factory()
    try:
        updated = TaskRepository(session).update_status(task_id, TaskStatus.COMPLETED)
        assert updated is not None
    finally:
        session.close()


def _list_report_artifacts(api_app: object, task_id: str) -> list[ReportData]:
    session = api_app.state.session_factory()
    try:
        artifacts = ArtifactRepository(session).list_by_task(
            task_id,
            REPORT_ARTIFACT_TYPE,
            ReportData,
        )
        return [ReportData.model_validate(artifact) for artifact in artifacts]
    finally:
        session.close()


def _list_word_report_artifacts(api_app: object, task_id: str) -> list[WordReport]:
    session = api_app.state.session_factory()
    try:
        artifacts = ArtifactRepository(session).list_by_task(
            task_id,
            WORD_REPORT_ARTIFACT_TYPE,
            WordReport,
        )
        return [WordReport.model_validate(artifact) for artifact in artifacts]
    finally:
        session.close()


def _list_markdown_report_artifacts(api_app: object, task_id: str) -> list[MarkdownReport]:
    session = api_app.state.session_factory()
    try:
        artifacts = ArtifactRepository(session).list_by_task(
            task_id,
            MARKDOWN_REPORT_ARTIFACT_TYPE,
            MarkdownReport,
        )
        return [MarkdownReport.model_validate(artifact) for artifact in artifacts]
    finally:
        session.close()


def _failing_workflow_factory():
    raise RuntimeError("report workflow should not run when cached report is locked")


def test_completed_task_can_get_web_report_data(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/report", headers={"X-Trace-Id": "trace_report"})

    payload = response.json()
    report = payload["data"]
    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["trace_id"] == "trace_report"
    assert report["task_id"] == task_id
    assert len(report["section_order"]) == 8
    assert report["section_order"] == [
        "conclusion_summary",
        "competitive_landscape_judgment",
        "core_competitor_analysis",
        "user_decision_chain_analysis",
        "target_opportunities_and_risks",
        "product_strategy_recommendations",
        "evidence_quality_appendix",
        "analysis_process_appendix",
    ]
    assert report["core_competitor_analysis"]["items"]
    assert _list_report_artifacts(api_app, task_id)[0].report_id == report["report_id"]


def test_report_get_reuses_locked_report_without_regenerating(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    first_response = client.get(f"/tasks/{task_id}/report")
    api_app.state.report_workflow_factory = _failing_workflow_factory
    second_response = client.get(f"/tasks/{task_id}/report")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["data"]["report_id"] == first_response.json()["data"][
        "report_id"
    ]
    assert len(_list_report_artifacts(api_app, task_id)) == 1


def test_report_regenerate_explicitly_creates_new_locked_version(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    first_response = client.get(f"/tasks/{task_id}/report")
    regenerate_response = client.post(f"/tasks/{task_id}/report/regenerate")
    next_get_response = client.get(f"/tasks/{task_id}/report")

    first_report_id = first_response.json()["data"]["report_id"]
    regenerated_report_id = regenerate_response.json()["data"]["report_id"]

    assert first_response.status_code == 200
    assert regenerate_response.status_code == 200
    assert regenerated_report_id != first_report_id
    assert regenerated_report_id.endswith("_002")
    assert next_get_response.json()["data"]["report_id"] == regenerated_report_id
    assert [report.report_id for report in _list_report_artifacts(api_app, task_id)] == [
        first_report_id,
        regenerated_report_id,
    ]


def test_completed_task_can_export_word_report(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/report/docx")

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert "filename=" in response.headers["content-disposition"]
    assert response.content[:2] == b"PK"
    assert api_app.state.report_output_dir.exists()
    Document(BytesIO(response.content))


def test_word_export_uses_current_locked_report_version(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    first_report_id = client.get(f"/tasks/{task_id}/report").json()["data"]["report_id"]
    first_docx_response = client.get(f"/tasks/{task_id}/report/docx")
    regenerated_report_id = client.post(f"/tasks/{task_id}/report/regenerate").json()["data"][
        "report_id"
    ]
    second_docx_response = client.get(f"/tasks/{task_id}/report/docx")

    word_reports = _list_word_report_artifacts(api_app, task_id)

    assert first_docx_response.status_code == 200
    assert second_docx_response.status_code == 200
    assert regenerated_report_id != first_report_id
    assert [word.report_id for word in word_reports] == [first_report_id, regenerated_report_id]


def test_unfinished_task_report_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)
    task_id = _create_task(client)

    response = client.get(f"/tasks/{task_id}/report")

    payload = response.json()
    assert response.status_code == 409
    assert payload["data"] is None
    assert payload["error"]["code"] == "REPORT_NOT_READY"
    assert payload["error"]["details"]["task_id"] == task_id
    assert payload["error"]["details"]["status"] == "created"


def test_unfinished_task_word_report_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)
    task_id = _create_task(client)

    response = client.get(f"/tasks/{task_id}/report/docx")

    payload = response.json()
    assert response.status_code == 409
    assert payload["data"] is None
    assert payload["error"]["code"] == "WORD_REPORT_NOT_READY"
    assert payload["error"]["details"]["task_id"] == task_id
    assert payload["error"]["details"]["status"] == "created"


def test_completed_task_can_export_markdown_report(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/report/markdown")

    payload = response.json()
    markdown_report = payload["data"]
    output_path = Path(markdown_report["file_path"])
    artifacts = _list_markdown_report_artifacts(api_app, task_id)

    assert response.status_code == 200
    assert payload["error"] is None
    assert markdown_report["task_id"] == task_id
    assert markdown_report["markdown_report_id"].startswith("markdown_report_") or (
        markdown_report["markdown_report_id"].startswith("markdown_")
    )
    assert "# 竞品分析报告" in markdown_report["markdown"]
    assert markdown_report["metadata"]["security_scan"] == "passed"
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == markdown_report["markdown"]
    assert [artifact.report_id for artifact in artifacts] == [markdown_report["report_id"]]
    sensitive_text = str(markdown_report)
    assert "API Key" not in sensitive_text
    assert "Cookie" not in sensitive_text
    assert "Authorization" not in sensitive_text


def test_word_export_failure_does_not_break_web_report(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    report_response = client.get(f"/tasks/{task_id}/report")
    blocked_output_dir = tmp_path / "blocked-output"
    blocked_output_dir.write_text("not a directory", encoding="utf-8")
    api_app.state.report_output_dir = blocked_output_dir

    docx_response = client.get(f"/tasks/{task_id}/report/docx")
    second_report_response = client.get(f"/tasks/{task_id}/report")
    trace_response = client.get(f"/tasks/{task_id}/trace")

    assert report_response.status_code == 200
    assert docx_response.status_code == 500
    assert docx_response.json()["error"]["code"] == "WORD_REPORT_EXPORT_FAILED"
    assert second_report_response.status_code == 200
    assert second_report_response.json()["data"]["report_id"] == report_response.json()["data"][
        "report_id"
    ]
    assert trace_response.status_code == 200
    trace_metadata = trace_response.json()["data"]["metadata"]
    failure = trace_metadata["last_failure"]
    assert failure["code"] == "WORD_REPORT_EXPORT_FAILED"
    assert failure["phase"] == "docx_render_or_write"
    assert failure["error_type"]
    assert failure["readable_reason"]
    assert trace_metadata["word_export_failures"][-1] == failure
    assert "blocked-output" not in str(trace_metadata)
    assert "not a directory" not in str(trace_metadata)


def test_missing_task_report_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    response = client.get("/tasks/task_missing/report")

    payload = response.json()
    assert response.status_code == 404
    assert payload["data"] is None
    assert payload["error"]["code"] == "TASK_NOT_FOUND"
    assert payload["error"]["details"]["task_id"] == "task_missing"
