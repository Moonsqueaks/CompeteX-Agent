import re
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from docx import Document
from docx.shared import Inches

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AnalysisTask,
    BattlefieldData,
    BattlefieldSliceSelection,
    Product,
    ProductRole,
    RelationshipGraphImage,
    ReportData,
    ReportSection,
    TaskStatus,
    TraceData,
    WordReport,
)
from app.schemas.common import JsonObject
from app.security import contains_sensitive_text, redact_sensitive_text, redact_sensitive_value
from app.services.battlefield_service import _battlefield_artifact_id, _build_battlefield_data
from app.services.markdown_renderer import DEFAULT_REPORTS_DIR
from app.services.relationship_graph_service import (
    RELATIONSHIP_GRAPH_ARTIFACT_TYPE,
    render_relationship_graph_png,
)
from app.services.report_service import REPORT_ARTIFACT_TYPE, redact_report_data
from app.services.trace_service import TRACE_ARTIFACT_TYPE, _build_trace_data, _trace_artifact_id
from app.storage import ArtifactRepository, TaskRepository

WORD_REPORT_ARTIFACT_TYPE = "word_report"
NO_RELIABLE_IMAGE = "暂无可靠图片"
NO_RELIABLE_DATA = "暂无可靠数据"
_WORD_REPORT_READABLE_STATUSES = {TaskStatus.COMPLETED, TaskStatus.HUMAN_REVIEWING}
_SAFE_FILE_STEM_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_RAW_ASSETS_DIR = _PROJECT_ROOT / "data" / "raw"
_RAW_ASSET_URL_PREFIX = "/assets/raw/"
_SUPPORTED_DOCX_IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpg", ".jpeg", ".png"}
_MAX_TEXT_CHARS = 600
_MAX_RENDERED_ITEMS = 18
_SECTION_TITLE_OVERRIDES = {
    "conclusion_summary": "结论摘要",
    "competitive_landscape_judgment": "竞争格局判断",
    "core_competitor_analysis": "核心竞品拆解",
    "user_decision_chain_analysis": "用户决策链分析",
    "target_opportunities_and_risks": "目标产品机会与风险",
    "product_strategy_recommendations": "产品策略建议",
    "evidence_quality_appendix": "证据与质检附录",
    "analysis_process_appendix": "分析流程与系统能力附录",
}

WorkflowFactory = Callable[[], Any]
GraphRenderer = Callable[..., Path]


class WordRenderError(ValueError):
    pass


class WordReportServiceError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class WordReportService:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        artifact_repository: ArtifactRepository,
        workflow_factory: WorkflowFactory = build_analysis_workflow,
        output_dir: Path | str | None = None,
        graph_renderer: GraphRenderer | None = None,
    ) -> None:
        self.task_repository = task_repository
        self.artifact_repository = artifact_repository
        self.workflow_factory = workflow_factory
        self.output_dir = output_dir
        self.graph_renderer = graph_renderer or render_relationship_graph_png

    def export_word_report(self, task_id: str) -> WordReport:
        task = self._get_completed_task(task_id)
        state = self._run_workflow(task)
        report = self._report_from_state(task, state)
        products = [Product.model_validate(item) for item in state.get("products", [])]
        battlefield = _build_battlefield_data(
            state,
            BattlefieldSliceSelection(),
            _battlefield_artifact_id(task.task_id, BattlefieldSliceSelection()),
        )
        graph_path, graph_metadata = self._render_relationship_graph(task, report, battlefield)

        try:
            word_report = render_word_report(
                report,
                products=products,
                battlefield=battlefield,
                relationship_graph_path=graph_path,
                output_dir=self.output_dir,
                extra_metadata=graph_metadata,
            )
        except Exception as exc:
            self._record_word_export_failure(
                task_id=task.task_id,
                report=report,
                phase="docx_render_or_write",
                exc=exc,
            )
            raise WordReportServiceError(
                "WORD_REPORT_EXPORT_FAILED",
                "Word report export failed",
                status_code=500,
                details={
                    "task_id": task.task_id,
                    "report_id": report.report_id,
                    "reason": exc.__class__.__name__,
                },
            ) from exc

        self.artifact_repository.save(
            WORD_REPORT_ARTIFACT_TYPE,
            word_report.word_report_id,
            word_report,
        )
        return word_report

    def _get_completed_task(self, task_id: str) -> AnalysisTask:
        task = self.task_repository.get(task_id)
        if task is None:
            raise WordReportServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task_id},
            )
        if task.status not in _WORD_REPORT_READABLE_STATUSES:
            raise WordReportServiceError(
                "WORD_REPORT_NOT_READY",
                "Word report is only available after completion or human review.",
                status_code=409,
                details={"task_id": task_id, "status": task.status.value},
            )
        return task

    def _run_workflow(self, task: AnalysisTask) -> Mapping[str, Any]:
        try:
            workflow = self.workflow_factory()
            state = create_initial_state(task)
            result = workflow.invoke(state)
        except Exception as exc:
            raise WordReportServiceError(
                "WORD_REPORT_DATA_FAILED",
                "Word report data generation failed",
                status_code=500,
                details={"task_id": task.task_id, "reason": exc.__class__.__name__},
            ) from exc

        if result["task"].get("status") != TaskStatus.COMPLETED.value or not result["reports"]:
            raise WordReportServiceError(
                "WORD_REPORT_DATA_FAILED",
                "Word report data generation did not produce a completed report.",
                status_code=500,
                details={
                    "task_id": task.task_id,
                    "workflow_status": result["task"].get("status"),
                },
            )
        return result

    def _report_from_state(self, task: AnalysisTask, state: Mapping[str, Any]) -> ReportData:
        report = redact_report_data(ReportData.model_validate(state["reports"][-1]))
        cached = self.artifact_repository.get(
            task.task_id,
            REPORT_ARTIFACT_TYPE,
            report.report_id,
            ReportData,
        )
        if cached is None:
            self.artifact_repository.save(REPORT_ARTIFACT_TYPE, report.report_id, report)
            return report
        return redact_report_data(ReportData.model_validate(cached))

    def _render_relationship_graph(
        self,
        task: AnalysisTask,
        report: ReportData,
        battlefield: BattlefieldData,
    ) -> tuple[Path | None, JsonObject]:
        file_name = f"{task.task_id}_{report.report_id}_competition_graph.png"
        try:
            graph_path = self.graph_renderer(
                battlefield,
                output_dir=self.output_dir,
                file_name=file_name,
            )
        except Exception as exc:
            return None, {
                "relationship_graph_status": "failed",
                "relationship_graph_failure_reason": exc.__class__.__name__,
            }

        graph_image = RelationshipGraphImage(
            graph_image_id=f"relationship_graph_{report.report_id}",
            task_id=task.task_id,
            report_id=report.report_id,
            generated_at=datetime.now(UTC),
            file_path=str(graph_path),
            file_name=graph_path.name,
            byte_size=graph_path.stat().st_size,
            metadata={
                "relation_count": len(battlefield.key_relations[:5]),
                "security_scan": "passed",
                "source": "word_report_export",
            },
        )
        self.artifact_repository.save(
            RELATIONSHIP_GRAPH_ARTIFACT_TYPE,
            graph_image.graph_image_id,
            graph_image,
        )
        return graph_path, {
            "relationship_graph_status": "generated",
            "relationship_graph_image_id": graph_image.graph_image_id,
            "relationship_graph_file_name": graph_image.file_name,
        }

    def _record_word_export_failure(
        self,
        *,
        task_id: str,
        report: ReportData,
        phase: str,
        exc: Exception,
    ) -> None:
        task = self.task_repository.get(task_id)
        if task is None:
            return

        cached = self.artifact_repository.get(
            task_id,
            TRACE_ARTIFACT_TYPE,
            _trace_artifact_id(task_id),
            TraceData,
        )
        if cached is None:
            trace = _build_trace_data(
                task=task,
                state=None,
                trace_view_id=_trace_artifact_id(task_id),
            )
        else:
            trace = TraceData.model_validate(cached)

        failure_record = {
            "status": "failed",
            "code": "WORD_REPORT_EXPORT_FAILED",
            "report_id": report.report_id,
            "phase": phase,
            "error_type": exc.__class__.__name__,
            "readable_reason": "Word 报告导出失败，请检查导出目录或文件写入权限。",
            "details": redact_sensitive_value(
                {
                    "task_id": task_id,
                    "report_id": report.report_id,
                    "phase": phase,
                },
                redact_key_names=True,
            ),
            "recorded_at": datetime.now(UTC).isoformat(),
        }
        metadata = dict(trace.metadata)
        failure_records = list(metadata.get("word_export_failures", []))
        failure_records.append(failure_record)
        metadata["word_export_failures"] = failure_records
        metadata["last_failure"] = failure_record
        updated_trace = TraceData.model_validate(
            {
                **trace.model_dump(mode="json"),
                "metadata": metadata,
                "generated_at": datetime.now(UTC).isoformat(),
            }
        )
        self.artifact_repository.save(
            TRACE_ARTIFACT_TYPE,
            updated_trace.trace_view_id,
            updated_trace,
        )


def render_word_report(
    report_data: ReportData | Mapping[str, Any],
    *,
    products: Sequence[Product | Mapping[str, Any]] = (),
    battlefield: BattlefieldData | Mapping[str, Any] | None = None,
    relationship_graph_path: Path | str | None = None,
    output_dir: Path | str | None = None,
    file_name: str | None = None,
    generated_at: datetime | None = None,
    extra_metadata: Mapping[str, Any] | None = None,
) -> WordReport:
    report = ReportData.model_validate(report_data)
    product_list = [Product.model_validate(product) for product in products]
    battlefield_data = (
        BattlefieldData.model_validate(battlefield) if battlefield is not None else None
    )
    exported_at = generated_at or datetime.now(UTC)

    document = Document()
    _set_core_properties(document, report)
    _append_cover(document, report, exported_at)
    _append_static_toc(document, report)
    _append_image_summary(document, product_list, battlefield_data)
    _append_relationship_graph(document, relationship_graph_path)
    _append_report_body(document, report)
    _assert_document_is_safe(document)

    report_dir = Path(output_dir) if output_dir is not None else DEFAULT_REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    output_path = report_dir / _safe_docx_file_name(
        file_name or f"{report.task_id}_{report.report_id}.docx"
    )
    document.save(output_path)

    metadata: JsonObject = {
        "section_count": len(report.section_order),
        "file_name": output_path.name,
        "byte_size": output_path.stat().st_size,
        "security_scan": "passed",
        "target_image_status": _image_status(_target_product(product_list)),
        "core_competitor_image_count": _core_competitor_image_count(product_list, battlefield_data),
        "relationship_graph_included": _valid_image_path(relationship_graph_path) is not None,
    }
    if extra_metadata:
        metadata.update(redact_sensitive_value(dict(extra_metadata), redact_key_names=True))

    return WordReport(
        word_report_id=f"word_{report.report_id}",
        task_id=report.task_id,
        report_id=report.report_id,
        generated_at=exported_at,
        file_path=str(output_path),
        file_name=output_path.name,
        byte_size=output_path.stat().st_size,
        metadata=metadata,
    )


def _set_core_properties(document, report: ReportData) -> None:
    document.core_properties.title = _safe_text("竞品分析报告")
    document.core_properties.subject = _safe_text(f"Task {report.task_id}")
    document.core_properties.keywords = "competitive-analysis,docx"


def _append_cover(document, report: ReportData, exported_at: datetime) -> None:
    document.add_heading(_safe_text("竞品分析报告"), 0)
    document.add_paragraph(_safe_text(f"任务 ID：{report.task_id}"))
    document.add_paragraph(_safe_text(f"报告 ID：{report.report_id}"))
    document.add_paragraph(_safe_text(f"报告生成时间：{report.generated_at.isoformat()}"))
    document.add_paragraph(_safe_text(f"Word 导出时间：{exported_at.isoformat()}"))
    document.add_page_break()


def _append_static_toc(document, report: ReportData) -> None:
    document.add_heading(_safe_text("目录"), level=1)
    document.add_paragraph(_safe_text("正文"))
    for index, section in enumerate(_ordered_sections(report), start=1):
        toc_line = f"{index}. {_section_title(section)}"
        document.add_paragraph(_safe_text(toc_line), style="List Number")
    document.add_page_break()


def _append_image_summary(
    document,
    products: Sequence[Product],
    battlefield: BattlefieldData | None,
) -> None:
    document.add_heading(_safe_text("产品图片摘要"), level=1)
    target_product = _target_product(products)
    _append_product_image_block(document, "目标产品缩略图", target_product)

    products_by_id = {product.product_id: product for product in products}
    competitor_ids = []
    if battlefield is not None:
        competitor_ids = [
            relation.competitor_product_id for relation in battlefield.key_relations[:3]
        ]
    document.add_heading(_safe_text("核心竞品缩略图"), level=2)
    if not competitor_ids:
        document.add_paragraph(_safe_text(NO_RELIABLE_IMAGE))
    for competitor_id in competitor_ids:
        competitor = products_by_id.get(competitor_id)
        _append_product_image_block(
            document,
            competitor.name if competitor is not None else competitor_id,
            competitor,
        )


def _append_product_image_block(document, title: str, product: Product | None) -> None:
    document.add_heading(_safe_text(title), level=2)
    if product is None:
        document.add_paragraph(_safe_text(NO_RELIABLE_IMAGE))
        return

    document.add_paragraph(_safe_text(product.name))
    image_path = _image_path_for_product(product)
    if image_path is None:
        document.add_paragraph(_safe_text(NO_RELIABLE_IMAGE))
        return
    if not _add_picture_or_placeholder(document, image_path, width_inches=1.35):
        document.add_paragraph(_safe_text(NO_RELIABLE_IMAGE))


def _append_relationship_graph(document, relationship_graph_path: Path | str | None) -> None:
    document.add_heading(_safe_text("简化竞争关系图"), level=1)
    image_path = _valid_image_path(relationship_graph_path)
    if image_path is None:
        document.add_paragraph(_safe_text(NO_RELIABLE_IMAGE))
        return
    if not _add_picture_or_placeholder(document, image_path, width_inches=6.2):
        document.add_paragraph(_safe_text(NO_RELIABLE_IMAGE))


def _append_report_body(document, report: ReportData) -> None:
    document.add_heading(_safe_text("正文"), level=1)
    for section in _ordered_sections(report):
        _append_section(document, section)


def _append_section(document, section: ReportSection) -> None:
    document.add_heading(_safe_text(_section_title(section)), level=1)
    document.add_paragraph(_safe_text(section.summary))
    if not section.items:
        document.add_paragraph(_safe_text(NO_RELIABLE_DATA))
    for item in section.items[:_MAX_RENDERED_ITEMS]:
        _append_item(document, item, depth=0)
    if len(section.items) > _MAX_RENDERED_ITEMS:
        document.add_paragraph(_safe_text("更多条目已折叠到网页报告中查看。"))
    if section.claim_ids:
        document.add_paragraph(_safe_text(f"Claim 索引：{', '.join(section.claim_ids)}"))
    if section.evidence_ids:
        document.add_paragraph(_safe_text(f"Evidence 索引：{', '.join(section.evidence_ids)}"))


def _append_item(document, item: Any, *, depth: int) -> None:
    redacted = redact_sensitive_value(item, redact_key_names=True)
    if isinstance(redacted, Mapping):
        _append_mapping(document, redacted, depth=depth)
        return
    if isinstance(redacted, list | tuple):
        for value in redacted[:_MAX_RENDERED_ITEMS]:
            _append_item(document, value, depth=depth + 1)
        return
    document.add_paragraph(_safe_text(_format_scalar(redacted)), style=_list_style(depth))


def _append_mapping(document, item: Mapping[str, Any], *, depth: int) -> None:
    for key, value in list(item.items())[:_MAX_RENDERED_ITEMS]:
        label = _safe_text(_humanize_key(str(key)))
        if isinstance(value, Mapping | list | tuple):
            document.add_paragraph(_safe_text(f"{label}："), style=_list_style(depth))
            _append_item(document, value, depth=depth + 1)
            continue
        document.add_paragraph(
            _safe_text(f"{label}：{_format_scalar(value)}"),
            style=_list_style(depth),
        )


def _add_picture_or_placeholder(document, image_path: Path, *, width_inches: float) -> bool:
    try:
        document.add_picture(str(image_path), width=Inches(width_inches))
    except Exception:
        return False
    return True


def _target_product(products: Sequence[Product]) -> Product | None:
    for product in products:
        if product.role == ProductRole.TARGET:
            return product
    return products[0] if products else None


def _core_competitor_image_count(
    products: Sequence[Product],
    battlefield: BattlefieldData | None,
) -> int:
    if battlefield is None:
        return 0
    products_by_id = {product.product_id: product for product in products}
    count = 0
    for relation in battlefield.key_relations[:3]:
        product = products_by_id.get(relation.competitor_product_id)
        if product is not None and _image_path_for_product(product) is not None:
            count += 1
    return count


def _image_status(product: Product | None) -> str:
    if product is None:
        return "missing"
    return "available" if _image_path_for_product(product) is not None else "missing"


def _image_path_for_product(product: Product) -> Path | None:
    for value in (
        product.primary_image_source_path,
        product.primary_image_path,
        product.primary_image_url,
    ):
        candidate = _resolve_local_image_path(value)
        if candidate is not None:
            return candidate
    return None


def _resolve_local_image_path(value: str | None) -> Path | None:
    if value is None or not value.strip():
        return None
    raw_value = value.strip()
    if raw_value.startswith(("http://", "https://")):
        return None
    if raw_value.startswith(_RAW_ASSET_URL_PREFIX):
        relative = unquote(raw_value.removeprefix(_RAW_ASSET_URL_PREFIX))
        return _valid_image_path(_RAW_ASSETS_DIR / relative, root=_RAW_ASSETS_DIR)
    path = Path(raw_value)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    return _valid_image_path(path, root=_PROJECT_ROOT)


def _valid_image_path(value: Path | str | None, *, root: Path | None = None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.suffix.lower() not in _SUPPORTED_DOCX_IMAGE_EXTENSIONS:
        return None
    try:
        resolved = path.resolve()
    except OSError:
        return None
    if root is not None:
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            return None
    if not resolved.exists() or not resolved.is_file():
        return None
    return resolved


def _ordered_sections(report: ReportData) -> list[ReportSection]:
    return [getattr(report, section_id) for section_id in report.section_order]


def _section_title(section: ReportSection) -> str:
    return _SECTION_TITLE_OVERRIDES.get(section.section_id, section.title)


def _assert_document_is_safe(document) -> None:
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    if contains_sensitive_text(text):
        raise WordRenderError("Word report export blocked by sensitive content scan.")


def _safe_docx_file_name(value: str) -> str:
    safe_value = redact_sensitive_text(Path(value).name)
    stem = _SAFE_FILE_STEM_PATTERN.sub("_", Path(safe_value).stem).strip("._")
    return f"{stem or 'report'}.docx"


def _safe_text(value: Any) -> str:
    redacted = redact_sensitive_text(str(value or ""))
    compact = " ".join(redacted.split())
    if len(compact) <= _MAX_TEXT_CHARS:
        return compact
    return compact[: _MAX_TEXT_CHARS - 3].rstrip() + "..."


def _format_scalar(value: Any) -> str:
    if value is None or value == "" or value == [] or value == {}:
        return NO_RELIABLE_DATA
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _humanize_key(key: str) -> str:
    return key.replace("_", " ").title()


def _list_style(depth: int) -> str:
    return "List Bullet 2" if depth > 0 else "List Bullet"
