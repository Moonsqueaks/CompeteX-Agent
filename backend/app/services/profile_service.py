from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from typing import Any

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AnalysisTask,
    CompetitionEdge,
    CompetitionType,
    Evidence,
    EvidenceSummary,
    FeatureTree,
    PricingEvidenceSummary,
    PricingModel,
    Product,
    ProductProfileComparison,
    ProductProfileData,
    ProductRole,
    ProfileComparisonDimension,
    ProfileComparisonDimensionKey,
    ProfileComparisonProduct,
    ProfileComparisonSlot,
    ProfileComparisonValue,
    RiskFlag,
    TargetComparisonStatus,
    TaskStatus,
    UserPersona,
)
from app.services.product_image_metadata import product_main_image_url
from app.storage import ArtifactRepository, TaskRepository

PRODUCT_PROFILE_ARTIFACT_TYPE = "product_profile"
MAX_EVIDENCE_SUMMARY_CHARS = 180
_PROFILE_READABLE_STATUSES = {TaskStatus.COMPLETED, TaskStatus.HUMAN_REVIEWING}

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
            return _hydrate_profile_product_images(cached_profile)
        return _hydrate_profile_product_images(self._generate_and_cache_profile(task))

    def _get_completed_task(self, task_id: str) -> AnalysisTask:
        task = self.task_repository.get(task_id)
        if task is None:
            raise ProfileServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task_id},
            )
        if task.status not in _PROFILE_READABLE_STATUSES:
            raise ProfileServiceError(
                "PROFILE_NOT_READY",
                "Product profile is only available after completion or human review.",
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
        profile = _hydrate_profile_product_images(profile)
        self.artifact_repository.save(PRODUCT_PROFILE_ARTIFACT_TYPE, profile.profile_id, profile)
        return profile


def _hydrate_profile_product_images(profile: ProductProfileData) -> ProductProfileData:
    product = _hydrate_product_image(profile.product)
    horizontal_comparison = profile.horizontal_comparison
    if horizontal_comparison is not None:
        compared_products = [
            _hydrate_profile_comparison_product_image(item)
            for item in horizontal_comparison.compared_products
        ]
        horizontal_comparison = horizontal_comparison.model_copy(
            update={"compared_products": compared_products},
        )

    if product == profile.product and horizontal_comparison == profile.horizontal_comparison:
        return profile
    return profile.model_copy(
        update={
            "product": product,
            "horizontal_comparison": horizontal_comparison,
        },
    )


def _hydrate_product_image(product: Product) -> Product:
    image_url = product_main_image_url(sku_id=product.sku_id, product_id=product.product_id)
    if image_url is None or image_url == product.primary_image_path:
        return product
    return product.model_copy(
        update={
            "primary_image_path": image_url,
            "primary_image_url": image_url,
            "primary_image_source_path": image_url,
        },
    )


def _hydrate_profile_comparison_product_image(
    product: ProfileComparisonProduct,
) -> ProfileComparisonProduct:
    image_url = product_main_image_url(product_id=product.product_id)
    if image_url is None or image_url == product.primary_image_path:
        return product
    return product.model_copy(update={"primary_image_path": image_url})


def _build_product_profile(state: dict[str, Any]) -> ProductProfileData:
    products = [Product.model_validate(item) for item in state["products"]]
    evidences = [Evidence.model_validate(item) for item in state["evidences"]]
    feature_trees = [FeatureTree.model_validate(item) for item in state["feature_trees"]]
    pricing_models = [PricingModel.model_validate(item) for item in state["pricing_models"]]
    user_personas = [UserPersona.model_validate(item) for item in state["user_personas"]]
    competition_edges = [
        CompetitionEdge.model_validate(item) for item in state.get("competition_edges", [])
    ]
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
        horizontal_comparison=_horizontal_comparison(
            task_id=task_id,
            products=products,
            evidences=evidences,
            feature_trees=feature_trees,
            pricing_models=pricing_models,
            user_personas=user_personas,
            competition_edges=competition_edges,
            target_product=target_product,
        ),
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


def _horizontal_comparison(
    *,
    task_id: str,
    products: Sequence[Product],
    evidences: Sequence[Evidence],
    feature_trees: Sequence[FeatureTree],
    pricing_models: Sequence[PricingModel],
    user_personas: Sequence[UserPersona],
    competition_edges: Sequence[CompetitionEdge],
    target_product: Product,
) -> ProductProfileComparison:
    products_by_id = {product.product_id: product for product in products}
    selected_products = _comparison_products(target_product, products_by_id, competition_edges)
    feature_by_product = {item.product_id: item for item in feature_trees}
    pricing_by_product = {item.product_id: item for item in pricing_models}
    persona_by_product = {item.product_id: item for item in user_personas}
    evidences_by_product = _evidences_by_product(evidences)

    return ProductProfileComparison(
        target_product_id=target_product.product_id,
        compared_products=[
            _comparison_product(slot, product) for slot, product in selected_products
        ],
        dimensions=[
            _comparison_dimension(
                task_id=task_id,
                dimension_key=ProfileComparisonDimensionKey.PRICE_BAND,
                dimension_label="价格带",
                selected_products=selected_products,
                value_resolver=lambda product: _price_band_value(product, pricing_by_product),
                target_status=_price_status(target_product, selected_products, pricing_by_product),
                status_reason="根据目标与已选竞品的到手价区间判断价格相对位置。",
            ),
            _comparison_dimension(
                task_id=task_id,
                dimension_key=ProfileComparisonDimensionKey.CORE_SELLING_POINTS,
                dimension_label="核心卖点",
                selected_products=selected_products,
                value_resolver=lambda product: _selling_point_value(product, feature_by_product),
                target_status=TargetComparisonStatus.PARITY,
                status_reason="各产品均有可追溯卖点，默认作为持平项进入第一屏对照。",
            ),
            _comparison_dimension(
                task_id=task_id,
                dimension_key=ProfileComparisonDimensionKey.PERSONA,
                dimension_label="主要人群",
                selected_products=selected_products,
                value_resolver=lambda product: _persona_value(product, persona_by_product),
                target_status=TargetComparisonStatus.PARITY,
                status_reason="主要人群来自画像推断，作为同场景讨论输入。",
            ),
            _comparison_dimension(
                task_id=task_id,
                dimension_key=ProfileComparisonDimensionKey.SCENARIO,
                dimension_label="使用场景",
                selected_products=selected_products,
                value_resolver=lambda product: _scenario_value(product, persona_by_product),
                target_status=TargetComparisonStatus.PARITY,
                status_reason="使用场景来自画像推断，需结合证据下钻阅读。",
            ),
            _comparison_dimension(
                task_id=task_id,
                dimension_key=ProfileComparisonDimensionKey.EVIDENCE_CREDIBILITY,
                dimension_label="证据可信状态",
                selected_products=selected_products,
                value_resolver=lambda product: _evidence_credibility_value(
                    product,
                    evidences_by_product,
                ),
                target_status=_evidence_status(
                    target_product,
                    selected_products,
                    evidences_by_product,
                ),
                status_reason="根据证据是否具备来源、访问时间和内容摘要判断可信状态。",
            ),
        ],
    )


def _comparison_products(
    target_product: Product,
    products_by_id: dict[str, Product],
    competition_edges: Sequence[CompetitionEdge],
) -> list[tuple[ProfileComparisonSlot, Product]]:
    selected: list[tuple[ProfileComparisonSlot, Product]] = [
        (ProfileComparisonSlot.TARGET, target_product)
    ]
    direct_edge = _top_edge(
        competition_edges,
        lambda edge: edge.competition_type == CompetitionType.DIRECT,
    )
    alternative_edge = _top_edge(
        competition_edges,
        lambda edge: edge.competition_type
        in {CompetitionType.ALTERNATIVE, CompetitionType.CHANNEL},
    )
    for slot, edge in (
        (ProfileComparisonSlot.HIGHEST_THREAT_DIRECT, direct_edge),
        (ProfileComparisonSlot.HIGHEST_THREAT_ALTERNATIVE, alternative_edge),
    ):
        if edge is None:
            continue
        product = products_by_id.get(edge.competitor_product_id)
        selected_product_ids = {item.product_id for _, item in selected}
        if product is not None and product.product_id not in selected_product_ids:
            selected.append((slot, product))
    return selected


def _top_edge(
    competition_edges: Sequence[CompetitionEdge],
    predicate: Callable[[CompetitionEdge], bool],
) -> CompetitionEdge | None:
    edges = [edge for edge in competition_edges if predicate(edge)]
    if not edges:
        return None
    return sorted(edges, key=lambda edge: edge.edge_score, reverse=True)[0]


def _comparison_product(
    slot: ProfileComparisonSlot,
    product: Product,
) -> ProfileComparisonProduct:
    return ProfileComparisonProduct(
        slot=slot,
        product_id=product.product_id,
        product_name=product.name,
        brand=product.brand,
        primary_image_path=product.primary_image_path,
        product_url=product.product_url,
    )


def _comparison_dimension(
    *,
    task_id: str,
    dimension_key: ProfileComparisonDimensionKey,
    dimension_label: str,
    selected_products: Sequence[tuple[ProfileComparisonSlot, Product]],
    value_resolver: Callable[[Product], str],
    target_status: TargetComparisonStatus,
    status_reason: str,
) -> ProfileComparisonDimension:
    values = [
        ProfileComparisonValue(
            product_id=product.product_id,
            value=value_resolver(product),
            evidence_ids=product.evidence_ids,
        )
        for _, product in selected_products
    ]
    evidence_ids = _dedupe(
        evidence_id for value in values for evidence_id in value.evidence_ids
    )
    return ProfileComparisonDimension(
        dimension_key=dimension_key,
        dimension_label=dimension_label,
        values=values,
        target_status=target_status,
        status_reason=status_reason,
        evidence_ids=evidence_ids,
        trace_refs=[f"profile:{task_id}:{dimension_key.value}"],
        risk_flags=(
            [RiskFlag.MISSING_EVIDENCE]
            if target_status == TargetComparisonStatus.INSUFFICIENT_EVIDENCE
            else []
        ),
    )


def _price_band_value(
    product: Product,
    pricing_by_product: dict[str, PricingModel],
) -> str:
    pricing = pricing_by_product.get(product.product_id)
    if pricing is not None and pricing.price_band:
        return pricing.price_band
    return _tag_price_band(product) or "暂无可靠数据"


def _selling_point_value(
    product: Product,
    feature_by_product: dict[str, FeatureTree],
) -> str:
    feature_tree = feature_by_product.get(product.product_id)
    if feature_tree is None:
        return "暂无可靠数据"
    items = _dedupe(
        [
            *feature_tree.cleaning_capability,
            *feature_tree.odor_control,
            *feature_tree.safety_features,
            *feature_tree.smart_features,
        ]
    )
    return "、".join(items[:4]) if items else "暂无可靠数据"


def _persona_value(
    product: Product,
    persona_by_product: dict[str, UserPersona],
) -> str:
    persona = persona_by_product.get(product.product_id)
    if persona is None or not persona.personas:
        return "暂无可靠数据"
    return "、".join(persona.personas[:3])


def _scenario_value(
    product: Product,
    persona_by_product: dict[str, UserPersona],
) -> str:
    persona = persona_by_product.get(product.product_id)
    if persona is None or not persona.scenarios:
        return "暂无可靠数据"
    return "、".join(persona.scenarios[:3])


def _evidence_credibility_value(
    product: Product,
    evidences_by_product: dict[str, list[Evidence]],
) -> str:
    evidences = evidences_by_product.get(product.product_id, [])
    if not evidences:
        return "证据不足"
    if any(evidence.access_time is None or evidence.source_url is None for evidence in evidences):
        return "谨慎参考"
    return "可直接采纳"


def _price_status(
    target_product: Product,
    selected_products: Sequence[tuple[ProfileComparisonSlot, Product]],
    pricing_by_product: dict[str, PricingModel],
) -> TargetComparisonStatus:
    target_price = _final_price(target_product, pricing_by_product)
    competitor_prices = [
        price
        for _, product in selected_products
        if product.product_id != target_product.product_id
        for price in [_final_price(product, pricing_by_product)]
        if price is not None
    ]
    if target_price is None or not competitor_prices:
        return TargetComparisonStatus.INSUFFICIENT_EVIDENCE
    lowest_competitor_price = min(competitor_prices)
    if target_price <= lowest_competitor_price * 0.95:
        return TargetComparisonStatus.ADVANTAGE
    if target_price > lowest_competitor_price * 1.10:
        return TargetComparisonStatus.WEAKNESS
    return TargetComparisonStatus.PARITY


def _evidence_status(
    target_product: Product,
    selected_products: Sequence[tuple[ProfileComparisonSlot, Product]],
    evidences_by_product: dict[str, list[Evidence]],
) -> TargetComparisonStatus:
    target_value = _evidence_credibility_value(target_product, evidences_by_product)
    competitor_values = [
        _evidence_credibility_value(product, evidences_by_product)
        for _, product in selected_products
        if product.product_id != target_product.product_id
    ]
    if target_value == "证据不足":
        return TargetComparisonStatus.INSUFFICIENT_EVIDENCE
    if competitor_values and all(value != "可直接采纳" for value in competitor_values):
        return TargetComparisonStatus.ADVANTAGE
    if competitor_values and any(value == "可直接采纳" for value in competitor_values):
        return TargetComparisonStatus.PARITY
    return TargetComparisonStatus.PARITY


def _final_price(
    product: Product,
    pricing_by_product: dict[str, PricingModel],
) -> float | None:
    pricing = pricing_by_product.get(product.product_id)
    return pricing.final_price if pricing is not None else None


def _evidences_by_product(evidences: Sequence[Evidence]) -> dict[str, list[Evidence]]:
    grouped: dict[str, list[Evidence]] = {}
    for evidence in evidences:
        if evidence.product_id is None:
            continue
        grouped.setdefault(evidence.product_id, []).append(evidence)
    return grouped


def _tag_price_band(product: Product) -> str | None:
    for tag in product.tags:
        if "-" in tag:
            return tag
    return None


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
