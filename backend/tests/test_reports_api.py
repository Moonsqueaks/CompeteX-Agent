from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import ReportData, TaskStatus
from app.services import REPORT_ARTIFACT_TYPE
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
    assert len(report["section_order"]) == 9
    assert report["competitor_findings"]["items"]
    assert _list_report_artifacts(api_app, task_id)[0].report_id == report["report_id"]


def test_completed_task_can_export_markdown_report(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/report/markdown")

    payload = response.json()
    markdown_report = payload["data"]
    output_path = Path(markdown_report["file_path"])
    assert response.status_code == 200
    assert payload["error"] is None
    assert markdown_report["task_id"] == task_id
    assert markdown_report["metadata"]["file_name"].endswith(".md")
    assert markdown_report["metadata"]["file_name"] == output_path.name
    assert "# 竞品分析报告" in markdown_report["markdown"]
    assert output_path.exists()
    assert output_path.parent == api_app.state.report_output_dir


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


def test_markdown_export_failure_does_not_break_web_report(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    report_response = client.get(f"/tasks/{task_id}/report")
    blocked_output_dir = tmp_path / "blocked-output"
    blocked_output_dir.write_text("not a directory", encoding="utf-8")
    api_app.state.report_output_dir = blocked_output_dir

    markdown_response = client.get(f"/tasks/{task_id}/report/markdown")
    second_report_response = client.get(f"/tasks/{task_id}/report")

    assert report_response.status_code == 200
    assert markdown_response.status_code == 500
    assert markdown_response.json()["error"]["code"] == "MARKDOWN_EXPORT_FAILED"
    assert second_report_response.status_code == 200
    assert second_report_response.json()["data"]["report_id"] == report_response.json()["data"][
        "report_id"
    ]


def test_missing_task_report_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    response = client.get("/tasks/task_missing/report")

    payload = response.json()
    assert response.status_code == 404
    assert payload["data"] is None
    assert payload["error"]["code"] == "TASK_NOT_FOUND"
    assert payload["error"]["details"]["task_id"] == "task_missing"
