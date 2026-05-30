import re
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AnalysisTask,
    BattlefieldData,
    BattlefieldGraphNode,
    BattlefieldKeyRelation,
    BattlefieldSliceSelection,
    ProductRole,
    RelationshipGraphImage,
    ReportData,
    TaskStatus,
    TraceData,
)
from app.security import redact_sensitive_text
from app.services.battlefield_service import _battlefield_artifact_id, _build_battlefield_data
from app.services.markdown_renderer import DEFAULT_REPORTS_DIR
from app.services.report_service import REPORT_ARTIFACT_TYPE
from app.services.trace_service import TRACE_ARTIFACT_TYPE, _build_trace_data, _trace_artifact_id
from app.storage import ArtifactRepository, TaskRepository

RELATIONSHIP_GRAPH_ARTIFACT_TYPE = "relationship_graph_image"
_GRAPH_READABLE_STATUSES = {TaskStatus.COMPLETED, TaskStatus.HUMAN_REVIEWING}
_SAFE_FILE_STEM_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")
_CANVAS_SIZE = (1200, 760)
_NODE_RADIUS = 18
_RELATION_LIMIT = 5

WorkflowFactory = Callable[[], Any]
GraphRenderer = Callable[..., Path]


class RelationshipGraphServiceError(Exception):
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


class RelationshipGraphService:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        artifact_repository: ArtifactRepository,
        workflow_factory: WorkflowFactory = build_analysis_workflow,
        output_dir: Path | str | None = None,
        renderer: GraphRenderer | None = None,
    ) -> None:
        self.task_repository = task_repository
        self.artifact_repository = artifact_repository
        self.workflow_factory = workflow_factory
        self.output_dir = output_dir
        self.renderer = renderer or render_relationship_graph_png

    def export_relationship_graph(self, task_id: str) -> RelationshipGraphImage:
        task = self._get_completed_task(task_id)
        state = self._run_workflow(task)
        report = self._report_from_state(task, state)
        battlefield = _build_battlefield_data(
            state,
            BattlefieldSliceSelection(),
            _battlefield_artifact_id(task.task_id, BattlefieldSliceSelection()),
        )
        file_name = f"{task.task_id}_{report.report_id}_competition_graph.png"

        try:
            output_path = self.renderer(
                battlefield,
                output_dir=self.output_dir,
                file_name=file_name,
            )
        except Exception as exc:
            self._record_relationship_graph_failure(task_id=task.task_id, report=report, exc=exc)
            raise RelationshipGraphServiceError(
                "RELATIONSHIP_GRAPH_RENDER_FAILED",
                "Relationship graph image export failed",
                status_code=500,
                details={
                    "task_id": task.task_id,
                    "report_id": report.report_id,
                    "reason": exc.__class__.__name__,
                },
            ) from exc

        image = RelationshipGraphImage(
            graph_image_id=f"relationship_graph_{report.report_id}",
            task_id=task.task_id,
            report_id=report.report_id,
            generated_at=datetime.now(UTC),
            file_path=str(output_path),
            file_name=output_path.name,
            byte_size=output_path.stat().st_size,
            metadata={
                "relation_count": len(battlefield.key_relations[:_RELATION_LIMIT]),
                "security_scan": "passed",
                "source": "battlefield_key_relations",
            },
        )
        self.artifact_repository.save(
            RELATIONSHIP_GRAPH_ARTIFACT_TYPE,
            image.graph_image_id,
            image,
        )
        return image

    def _get_completed_task(self, task_id: str) -> AnalysisTask:
        task = self.task_repository.get(task_id)
        if task is None:
            raise RelationshipGraphServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task_id},
            )
        if task.status not in _GRAPH_READABLE_STATUSES:
            raise RelationshipGraphServiceError(
                "RELATIONSHIP_GRAPH_NOT_READY",
                "Relationship graph is only available after completion or human review.",
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
            raise RelationshipGraphServiceError(
                "RELATIONSHIP_GRAPH_DATA_FAILED",
                "Relationship graph data generation failed",
                status_code=500,
                details={"task_id": task.task_id, "reason": exc.__class__.__name__},
            ) from exc

        if result["task"].get("status") != TaskStatus.COMPLETED.value or not result["reports"]:
            raise RelationshipGraphServiceError(
                "RELATIONSHIP_GRAPH_DATA_FAILED",
                "Relationship graph data generation did not produce a completed report.",
                status_code=500,
                details={
                    "task_id": task.task_id,
                    "workflow_status": result["task"].get("status"),
                },
            )
        return result

    def _report_from_state(self, task: AnalysisTask, state: Mapping[str, Any]) -> ReportData:
        report = ReportData.model_validate(state["reports"][-1])
        cached = self.artifact_repository.get(
            task.task_id,
            REPORT_ARTIFACT_TYPE,
            report.report_id,
            ReportData,
        )
        if cached is None:
            self.artifact_repository.save(REPORT_ARTIFACT_TYPE, report.report_id, report)
            return report
        return ReportData.model_validate(cached)

    def _record_relationship_graph_failure(
        self,
        *,
        task_id: str,
        report: ReportData,
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

        metadata = dict(trace.metadata)
        failure_records = list(metadata.get("relationship_graph_failures", []))
        failure_records.append(
            {
                "status": "failed",
                "code": "RELATIONSHIP_GRAPH_RENDER_FAILED",
                "report_id": report.report_id,
                "reason": exc.__class__.__name__,
                "recorded_at": datetime.now(UTC).isoformat(),
            }
        )
        metadata["relationship_graph_failures"] = failure_records
        metadata["last_failure"] = failure_records[-1]
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


def render_relationship_graph_png(
    battlefield_data: BattlefieldData | Mapping[str, Any],
    *,
    output_dir: Path | str | None = None,
    file_name: str | None = None,
) -> Path:
    battlefield = BattlefieldData.model_validate(battlefield_data)
    report_dir = Path(output_dir) if output_dir is not None else DEFAULT_REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    output_path = report_dir / _safe_png_file_name(
        file_name or f"{battlefield.task_id}_{battlefield.battlefield_id}_competition_graph.png"
    )

    image = Image.new("RGB", _CANVAS_SIZE, "#FAFBFC")
    draw = ImageDraw.Draw(image)
    fonts = _load_fonts()
    _draw_header(draw, battlefield, fonts)
    _draw_graph(draw, battlefield, fonts)
    image.save(output_path, format="PNG")
    return output_path


def _draw_header(
    draw: ImageDraw.ImageDraw,
    battlefield: BattlefieldData,
    fonts: dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont],
) -> None:
    title = "Competition Relationship Graph"
    subtitle = (
        f"Task {battlefield.task_id} | key relations "
        f"{min(len(battlefield.key_relations), _RELATION_LIMIT)}"
    )
    draw.text((54, 36), title, fill="#172033", font=fonts["title"])
    draw.text((56, 82), _safe_text(subtitle, max_chars=110), fill="#5E6B85", font=fonts["small"])
    draw.line((54, 120, 1146, 120), fill="#D7DDE8", width=2)


def _draw_graph(
    draw: ImageDraw.ImageDraw,
    battlefield: BattlefieldData,
    fonts: dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont],
) -> None:
    target_node = _target_node(battlefield)
    target_box = (64, 316, 390, 446)
    _draw_node(
        draw,
        target_box,
        title="Target",
        body=target_node.label if target_node is not None else "Target product",
        accent="#2563EB",
        fonts=fonts,
    )

    relations = list(battlefield.key_relations[:_RELATION_LIMIT])
    if not relations:
        _draw_placeholder(draw, target_box, fonts)
        return

    y_positions = _relation_y_positions(len(relations))
    for relation, center_y in zip(relations, y_positions, strict=True):
        competitor_box = (806, center_y - 54, 1136, center_y + 54)
        line_color = _threat_color(relation.threat_level.value)
        _draw_connection(draw, target_box, competitor_box, center_y, relation, line_color, fonts)
        _draw_node(
            draw,
            competitor_box,
            title=_threat_label(relation.threat_level.value),
            body=relation.competitor_product_name,
            accent=line_color,
            fonts=fonts,
        )


def _draw_node(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    title: str,
    body: str,
    accent: str,
    fonts: dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont],
) -> None:
    draw.rounded_rectangle(box, radius=_NODE_RADIUS, fill="#FFFFFF", outline="#CAD3E1", width=2)
    draw.rounded_rectangle(
        (box[0], box[1], box[0] + 12, box[3]),
        radius=_NODE_RADIUS,
        fill=accent,
    )
    title_text = _safe_text(title, max_chars=36)
    body_text = _safe_text(body, max_chars=54)
    draw.text((box[0] + 28, box[1] + 20), title_text, fill=accent, font=fonts["label"])
    body_lines = _wrap_text(draw, body_text, fonts["body"], box[2] - box[0] - 48, 2)
    for index, line in enumerate(body_lines):
        draw.text(
            (box[0] + 28, box[1] + 52 + index * 25),
            line,
            fill="#172033",
            font=fonts["body"],
        )


def _draw_connection(
    draw: ImageDraw.ImageDraw,
    target_box: tuple[int, int, int, int],
    competitor_box: tuple[int, int, int, int],
    center_y: int,
    relation: BattlefieldKeyRelation,
    line_color: str,
    fonts: dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont],
) -> None:
    start = (target_box[2], (target_box[1] + target_box[3]) // 2)
    end = (competitor_box[0], center_y)
    elbow_x = 560
    draw.line(
        (start[0], start[1], elbow_x, start[1], elbow_x, end[1], end[0], end[1]),
        fill=line_color,
        width=4,
    )
    draw.ellipse((end[0] - 7, end[1] - 7, end[0] + 7, end[1] + 7), fill=line_color)

    label_box = (448, center_y - 35, 742, center_y + 35)
    draw.rounded_rectangle(label_box, radius=14, fill="#FFFFFF", outline=line_color, width=2)
    label = _safe_text(relation.relationship_label.value.replace("_", " "), max_chars=34)
    credibility = _safe_text(
        relation.evidence_credibility.value.value.replace("_", " "),
        max_chars=36,
    )
    draw.text((label_box[0] + 16, label_box[1] + 10), label, fill="#172033", font=fonts["label"])
    draw.text(
        (label_box[0] + 16, label_box[1] + 38),
        f"Evidence: {credibility}",
        fill="#5E6B85",
        font=fonts["small"],
    )


def _draw_placeholder(
    draw: ImageDraw.ImageDraw,
    target_box: tuple[int, int, int, int],
    fonts: dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont],
) -> None:
    placeholder_box = (486, 310, 1082, 456)
    draw.line(
        (
            target_box[2],
            (target_box[1] + target_box[3]) // 2,
            placeholder_box[0],
            (placeholder_box[1] + placeholder_box[3]) // 2,
        ),
        fill="#94A3B8",
        width=3,
    )
    draw.rounded_rectangle(placeholder_box, radius=18, fill="#FFFFFF", outline="#CBD5E1", width=2)
    draw.text(
        (placeholder_box[0] + 26, placeholder_box[1] + 34),
        "No reliable key competitor relationship",
        fill="#172033",
        font=fonts["label"],
    )
    draw.text(
        (placeholder_box[0] + 26, placeholder_box[1] + 72),
        "Placeholder generated; web report remains readable.",
        fill="#5E6B85",
        font=fonts["body"],
    )


def _target_node(battlefield: BattlefieldData) -> BattlefieldGraphNode | None:
    target_product_id = battlefield.metadata.get("target_product_id")
    for node in battlefield.graph_nodes:
        if node.role == ProductRole.TARGET:
            return node
    for node in battlefield.graph_nodes:
        if node.product_id == target_product_id:
            return node
    return battlefield.graph_nodes[0] if battlefield.graph_nodes else None


def _relation_y_positions(count: int) -> list[int]:
    if count == 1:
        return [382]
    top = 188
    bottom = 604
    step = (bottom - top) / (count - 1)
    return [round(top + step * index) for index in range(count)]


def _load_fonts() -> dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    font_path = _font_path()
    if font_path is None:
        default_font = ImageFont.load_default()
        return {
            "title": default_font,
            "label": default_font,
            "body": default_font,
            "small": default_font,
        }
    return {
        "title": ImageFont.truetype(font_path, 34),
        "label": ImageFont.truetype(font_path, 22),
        "body": ImageFont.truetype(font_path, 20),
        "small": ImageFont.truetype(font_path, 17),
    }


def _font_path() -> str | None:
    candidates = [
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    tokens = text.split()
    if len(tokens) <= 1:
        tokens = list(text)
    lines: list[str] = []
    current = ""
    for token in tokens:
        separator = " " if current and len(token) > 1 else ""
        candidate = f"{current}{separator}{token}" if current else token
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = token
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if not lines:
        lines = [""]
    if len(lines) == max_lines and _text_width(draw, lines[-1], font) > max_width:
        lines[-1] = _ellipsize(draw, lines[-1], font, max_width)
    elif len(lines) == max_lines and tokens:
        consumed = "".join(lines).replace(" ", "")
        if len(consumed) < len(text.replace(" ", "")):
            lines[-1] = _ellipsize(draw, lines[-1], font, max_width)
    return lines


def _text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> int:
    bbox = draw.textbbox((0, 0), _drawable_text(text, font), font=font)
    return bbox[2] - bbox[0]


def _ellipsize(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> str:
    suffix = "..."
    trimmed = text
    while trimmed and _text_width(draw, f"{trimmed}{suffix}", font) > max_width:
        trimmed = trimmed[:-1]
    return f"{trimmed.rstrip()}{suffix}" if trimmed else suffix


def _drawable_text(text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> str:
    try:
        font.getbbox(text)
    except UnicodeEncodeError:
        return text.encode("ascii", "replace").decode("ascii")
    return text


def _safe_text(value: Any, *, max_chars: int) -> str:
    redacted = redact_sensitive_text(str(value or ""))
    compact = " ".join(redacted.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def _threat_color(threat_level: str) -> str:
    colors = {
        "high_threat": "#DC2626",
        "medium_threat": "#D97706",
        "low_threat": "#64748B",
        "high_score_needs_review": "#7C3AED",
    }
    return colors.get(threat_level, "#64748B")


def _threat_label(threat_level: str) -> str:
    labels = {
        "high_threat": "High threat",
        "medium_threat": "Medium threat",
        "low_threat": "Low threat",
        "high_score_needs_review": "Needs review",
    }
    return labels.get(threat_level, "Threat")


def _safe_png_file_name(value: str) -> str:
    safe_value = redact_sensitive_text(Path(value).name)
    stem = _SAFE_FILE_STEM_PATTERN.sub("_", Path(safe_value).stem).strip("._")
    return f"{stem or 'competition_graph'}.png"
