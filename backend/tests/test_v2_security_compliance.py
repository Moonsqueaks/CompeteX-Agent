from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi.testclient import TestClient

from app.graph import build_analysis_workflow
from app.main import create_app
from app.schemas import ReportData, TaskStatus
from app.services import REPORT_ARTIFACT_TYPE
from app.storage import ArtifactRepository, TaskRepository

SENSITIVE_SNIPPETS = (
    "should-not-leak",
    "sk-secret123456789",
    "internal-secret",
    "13800138000",
    "acct-private-001",
    "北京市朝阳区幸福路88号3单元501室",
    "api_key",
)


def _client(tmp_path: Path) -> tuple[TestClient, object]:
    database_url = f"sqlite:///{(tmp_path / 'v2_security.db').as_posix()}"
    api_app = create_app(database_url=database_url)
    api_app.state.report_output_dir = tmp_path / "reports"
    return TestClient(api_app), api_app


def _create_task(client: TestClient, **overrides) -> str:
    payload = {
        "target_product_name": "安全回归目标",
        "target_product_url": "https://example.com/security",
        "category": "smart_pet_hardware",
        "subcategory": "automatic_litter_box",
        "data_source_mode": "demo_snapshot",
        "research_text": None,
    }
    payload.update(overrides)
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    return response.json()["data"]["task_id"]


def _mark_completed(api_app: object, task_id: str) -> None:
    session = api_app.state.session_factory()
    try:
        updated = TaskRepository(session).update_status(task_id, TaskStatus.COMPLETED)
        assert updated is not None
    finally:
        session.close()


def _cached_reports(api_app: object, task_id: str) -> list[ReportData]:
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


class SensitiveWorkflow:
    def invoke(self, state):
        result = build_analysis_workflow().invoke(state)
        report = result["reports"][-1]
        report["conclusion_summary"]["summary"] = (
            "api_key=should-not-leak sk-secret123456789 token=internal-secret "
            "手机 13800138000 account_id=acct-private-001 "
            "地址: 北京市朝阳区幸福路88号3单元501室"
        )
        report["conclusion_summary"]["items"].append(
            {
                "address": "北京市朝阳区幸福路88号3单元501室",
                "note": "Bearer should-not-leak token=internal-secret",
                "open_id": "acct-private-001",
            }
        )
        result["products"][0]["name"] = "目标产品 sk-secret123456789"
        return result


def test_web_report_and_cached_report_redact_sensitive_content(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    api_app.state.report_workflow_factory = SensitiveWorkflow
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/report")

    response_text = response.text
    assert response.status_code == 200
    assert "[REDACTED]" in response_text
    for snippet in SENSITIVE_SNIPPETS:
        assert snippet not in response_text

    cached_text = "\n".join(
        report.model_dump_json() for report in _cached_reports(api_app, task_id)
    )
    assert "[REDACTED]" in cached_text
    for snippet in SENSITIVE_SNIPPETS:
        assert snippet not in cached_text


def test_word_report_text_redacts_sensitive_content(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    api_app.state.word_report_workflow_factory = SensitiveWorkflow
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/report/docx")

    assert response.status_code == 200
    text = "\n".join(p.text for p in Document(BytesIO(response.content)).paragraphs)
    assert "自动猫砂盆竞品分析报告" in text
    for snippet in SENSITIVE_SNIPPETS:
        assert snippet not in text


def test_trace_and_export_failure_records_redact_sensitive_content(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(
        client,
        research_text=(
            "api_key=should-not-leak sk-secret123456789 token=internal-secret "
            "手机 13800138000 account_id=acct-private-001 "
            "地址: 北京市朝阳区幸福路88号3单元501室"
        ),
    )
    _mark_completed(api_app, task_id)

    trace_response = client.get(f"/tasks/{task_id}/trace")
    blocked_output_dir = tmp_path / "blocked-output"
    blocked_output_dir.write_text("not a directory", encoding="utf-8")
    api_app.state.report_output_dir = blocked_output_dir
    failure_response = client.get(f"/tasks/{task_id}/report/docx")
    trace_after_failure_response = client.get(f"/tasks/{task_id}/trace")

    assert trace_response.status_code == 200
    assert failure_response.status_code == 500
    assert trace_after_failure_response.status_code == 200
    combined_text = "\n".join(
        [trace_response.text, failure_response.text, trace_after_failure_response.text]
    )
    assert "[REDACTED]" in combined_text
    for snippet in SENSITIVE_SNIPPETS:
        assert snippet not in combined_text
    failure_metadata = trace_after_failure_response.json()["data"]["metadata"]
    failure = failure_metadata["last_failure"]
    assert failure["code"] == "WORD_REPORT_EXPORT_FAILED"
    assert failure_metadata["word_export_failures"][-1] == failure
    assert "blocked-output" not in str(failure_metadata)
    assert "not a directory" not in str(failure_metadata)
