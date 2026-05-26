from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from typing import Any

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AnalysisTask,
    Evidence,
    EvidenceSummary,
    FeatureTree,
    PricingEvidenceSummary,
    PricingModel,
    Product,
    ProductProfileData,
    ProductRole,
    RiskFlag,
    TaskStatus,
    UserPersona,
)
from app.storage import ArtifactRepository, TaskRepository

PRODUCT_PROFILE_ARTIFACT_TYPE = "product_profile"
MAX_EVIDENCE_SUMMARY_CHARS = 180

WorkflowFactory = Callable[[], Any]


class ProfileServiceError(Exception):
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


class ProfileService:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        artifact_repository: ArtifactRepository,
        workflow_factory: WorkflowFactory = build_analysis_workflow,
    ) -> None:
        self.task_repository = task_repository
        self.artifact_repository = artifact_repository
        self.workflow_factory = workflow_factory

    def get_product_profile(self, task_id: str) -> ProductProfileData:
        task = self._get_completed_task(task_id)
        cached_profile = self._latest_profile(task_id)
        if cached_profile is not None:
            return cached_profile
        return self._generate_and_cache_profile(task)

    def _get_completed_task(self, task_id: str) -> AnalysisTask:
        task = self.task_repository.get(task_id)
        if task is None:
            raise ProfileServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task_id},
            )
        if task.status != TaskStatus.COMPLETED:
            raise ProfileServiceError(
                "PROFILE_NOT_READY",
                "Product profile is only available after the task is completed.",
                status_code=409,
                details={"task_id": task_id, "status": task.status.value},
            )
        return task

    def _latest_profile(self, task_id: str) -> ProductProfileData | None:
        profiles = self.artifact_repository.list_by_task(
            task_id,
            PRODUCT_PROFILE_ARTIFACT_TYPE,
            ProductProfileData,
        )
        if not profiles:
            return None
        return ProductProfileData.model_validate(profiles[-1])

    def _generate_and_cache_profile(self, task: AnalysisTask) -> ProductProfileData:
        try:
            workflow = self.workflow_factory()
            state = create_initial_state(task)
            result = workflow.invoke(state)
        except Exception as exc:
            raise ProfileServiceError(
                "PROFILE_GENERATION_FAILED",
                "Product profile generation failed",
                status_code=500,
                details={"task_id": task.task_id, "reason": exc.__class__.__name__},
            ) from exc

        if result["task"].get("status") != TaskStatus.COMPLETED.value:
            raise ProfileServiceError(
                "PROFILE_GENERATION_FAILED",
                "Product profile generation did not complete the workflow.",
                status_code=500,
                details={
                    "task_id": task.task_id,
                    "workflow_status": result["task"].get("status"),
                },
            )

        profile = _build_product_profile(result)
        self.artifact_repository.save(PRODUCT_PROFILE_ARTIFACT_TYPE, profile.profile_id, profile)
        return profile


def _build_product_profile(state: dict[str, Any]) -> ProductProfileData:
    products = [Product.model_validate(item) for item in state["products"]]
    evidences = [Evidence.model_validate(item) for item in state["evidences"]]
    feature_trees = [FeatureTree.model_validate(item) for item in state["feature_trees"]]
    pricing_models = [PricingModel.model_validate(item) for item in state["pricing_models"]]
    user_personas = [UserPersona.model_validate(item) for item in state["user_personas"]]
    task_id = str(state["task"]["task_id"])

    target_product = _target_product(products)
    feature_tree = _first_for_product(feature_trees, target_product.product_id, "FeatureTree")
    pricing_model = _first_for_product(pricing_models, target_product.product_id, "PricingModel")
    user_persona = _first_for_product(user_personas, target_product.product_id, "UserPersona")
    evidence_ids = _dedupe(
        [
            *target_product.evidence_ids,
            *feature_tree.evidence_ids,
            *pricing_model.evidence_ids,
            *user_persona.evidence_ids,
        ]
    )
    target_evidences = [
        evidence
        for evidence in evidences
        if evidence.evidence_id in evidence_ids or evidence.product_id == target_product.product_id
    ]

    return ProductProfileData(
        profile_id=f"profile_{task_id}_{target_product.product_id}",
        task_id=task_id,
        generated_at=datetime.now(UTC),
        product=target_product,
        feature_tree=feature_tree,
        pricing_model=pricing_model,
        pricing_evidence=_pricing_evidence_summary(pricing_model),
        user_persona=user_persona,
        evidence_summaries=[_evidence_summary(evidence) for evidence in target_evidences],
        metadata={
            "target_product_id": target_product.product_id,
            "evidence_count": len(target_evidences),
            "source": "langgraph_workflow",
        },
    )


def _target_product(products: Sequence[Product]) -> Product:
    for product in products:
        if product.role == ProductRole.TARGET:
            return product
    raise ProfileServiceError(
        "PROFILE_GENERATION_FAILED",
        "Product profile generation did not produce a target product.",
        status_code=500,
    )


def _first_for_product[T](items: Sequence[T], product_id: str, label: str) -> T:
    for item in items:
        if getattr(item, "product_id", None) == product_id:
            return item
    raise ProfileServiceError(
        "PROFILE_GENERATION_FAILED",
        f"Product profile generation did not produce {label}.",
        status_code=500,
        details={"product_id": product_id},
    )


def _pricing_evidence_summary(pricing_model: PricingModel) -> PricingEvidenceSummary:
    return PricingEvidenceSummary(
        evidence_ids=pricing_model.evidence_ids,
        access_time=pricing_model.access_time,
        access_time_status=_access_time_status(pricing_model.access_time),
        risk_flags=pricing_model.risk_flags,
    )


def _evidence_summary(evidence: Evidence) -> EvidenceSummary:
    risk_flags = []
    if evidence.access_time is None:
        risk_flags.append(RiskFlag.MISSING_ACCESS_TIME)
    if evidence.screenshot_path is None:
        risk_flags.append(RiskFlag.MISSING_SCREENSHOT)
    return EvidenceSummary(
        evidence_id=evidence.evidence_id,
        product_id=evidence.product_id,
        source_type=evidence.source_type,
        source_url=evidence.source_url,
        screenshot_path=evidence.screenshot_path,
        access_time=evidence.access_time,
        access_time_status=_access_time_status(evidence.access_time),
        confidence_level=evidence.confidence_level,
        content_summary=_shorten(evidence.content_summary),
        limitations=_shorten(evidence.limitations),
        risk_flags=_dedupe(risk_flags),
    )


def _access_time_status(access_time: datetime | None) -> str:
    return "available" if access_time is not None else "missing"


def _shorten(value: str) -> str:
    compact = " ".join(value.split())
    if len(compact) <= MAX_EVIDENCE_SUMMARY_CHARS:
        return compact
    return compact[: MAX_EVIDENCE_SUMMARY_CHARS - 3].rstrip() + "..."


def _dedupe[T](items: Iterable[T]) -> list[T]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped
