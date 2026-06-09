import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  FloatButton,
  Form,
  Input,
  List,
  Row,
  Select,
  Space,
  Typography
} from "antd";
import { DollarSign, Edit3, Layers, Users, Zap } from "lucide-react";

import { navigateTo, routePathForTask, type AppRoute } from "../app/routes";
import { RequestStateMessage, createErrorState, createIdleState } from "../api";
import type { ApiClient, ApiRequestState, components } from "../api";
import {
  PROFILE_COMPARISON_EMPTY_LABELS,
  PROFILE_COMPARISON_SLOT_LABELS,
  PROFILE_COMPARISON_STATUS_LABELS
} from "../domain/labels";
import { EvidenceCard } from "../components/EvidenceCard";
import { PageEmptyState } from "../components/PageEmptyState";
import { PageLoadingState } from "../components/PageLoadingState";
import { RiskFlagList } from "../components/RiskFlagList";
import { StatusBadge } from "../components/StatusBadge";
import { resolveBackendAssetUrl } from "../utils/assets";
import { formatDateTime, formatNullable, formatPrice } from "../utils/format";
import { sanitizeTraceText } from "../utils/sanitize";

const { Text } = Typography;

type TaskApiClient = Pick<ApiClient, "get" | "post">;
type ProductProfileData = components["schemas"]["ProductProfileData"];
type ProductProfileComparison = components["schemas"]["ProductProfileComparison"];
type ProfileComparisonDimension = components["schemas"]["ProfileComparisonDimension"];
type ProfileComparisonProduct = components["schemas"]["ProfileComparisonProduct"];
type ProfileComparisonSlot = components["schemas"]["ProfileComparisonSlot"];
type HumanFeedbackCreateRequest = components["schemas"]["HumanFeedbackCreateRequest"];
type HumanFeedbackCreateResponse = components["schemas"]["HumanFeedbackCreateResponse"];

type HumanReviewOption = {
  currentValue: string | string[] | null | undefined;
  field: string;
  isList?: boolean;
  key: string;
  label: string;
  targetId: string;
  targetType: HumanFeedbackCreateRequest["target_type"];
};

type HumanReviewFormValues = {
  fieldKey: string;
  reason: string;
  value: string;
};

const EMPTY_VALUE_TEXT = "暂无可靠数据";
const PROFILE_COMPARISON_SLOT_ORDER: ProfileComparisonSlot[] = [
  "target",
  "highest_threat_direct_competitor",
  "highest_threat_alternative"
];

export function ProfilePage({
  apiClient,
  route,
  taskId
}: {
  apiClient: TaskApiClient;
  route: AppRoute;
  taskId: string | null;
}) {
  const [isReviewDrawerOpen, setIsReviewDrawerOpen] = useState(false);
  const profileQuery = useQuery({
    enabled: Boolean(taskId),
    queryFn: () =>
      apiClient.get<ProductProfileData>(`/tasks/${encodeURIComponent(taskId ?? "")}/profile`),
    queryKey: ["product-profile", taskId],
    retry: false
  });
  const profileState = toQueryRequestState(profileQuery);
  const profile = profileQuery.data;

  return (
    <section className="page-surface profile-page-surface" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">产品画像</p>
        <h3 id="page-title">{route.title}</h3>
        <p>{route.summary}</p>
      </div>

      {!taskId ? (
        <PageEmptyState />
      ) : null}

      {taskId ? (
        <div className="profile-modern-stack">
          {profileState.status === "loading" || profileState.status === "retrying" ? null : (
            <RequestStateMessage
              className="profile-state-message"
              loadingText="正在读取产品画像"
              onRetry={() => void profileQuery.refetch()}
              state={profileState}
            />
          )}

          {profileQuery.isFetching && !profile ? (
            <PageLoadingState text="正在读取产品画像" />
          ) : null}

          {profile ? (
            <>
              <Space direction="vertical" size="large" style={{ width: "100%" }}>
                <ProfileComparisonWorkbench profile={profile} taskId={taskId} />
                <Row gutter={[18, 18]} align="stretch">
                  <Col xs={24} lg={12}>
                    <ProductBasicsCard profile={profile} />
                  </Col>
                  <Col xs={24} lg={12}>
                    <PricingModelCard profile={profile} />
                  </Col>
                </Row>
                <Row gutter={[18, 18]} align="stretch">
                  <Col xs={24} lg={12}>
                    <FeatureTreeCard profile={profile} />
                  </Col>
                  <Col xs={24} lg={12}>
                    <UserPersonaCard profile={profile} />
                  </Col>
                </Row>
                <EvidenceSummaryCard profile={profile} />
              </Space>

              <FloatButton
                aria-label="修正画像"
                className="profile-review-float"
                icon={<Edit3 size={18} />}
                onClick={() => setIsReviewDrawerOpen(true)}
                tooltip="修正画像"
                type="primary"
              />

              <HumanReviewDrawer
                apiClient={apiClient}
                onClose={() => setIsReviewDrawerOpen(false)}
                onSubmitted={() => void profileQuery.refetch()}
                open={isReviewDrawerOpen}
                profile={profile}
                taskId={taskId}
              />
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function ProfileComparisonWorkbench({
  profile,
  taskId
}: {
  profile: ProductProfileData;
  taskId: string;
}) {
  const comparison = profile.horizontal_comparison ?? createTargetOnlyProfileComparison(profile);
  const productsBySlot = new Map(
    (comparison.compared_products ?? []).map((product) => [product.slot, product])
  );
  const visibleProducts = PROFILE_COMPARISON_SLOT_ORDER.map(
    (slot) => productsBySlot.get(slot) ?? null
  );

  return (
    <Card
      bordered={false}
      className="profile-panel profile-panel-wide profile-comparison-workbench"
      title={
        <div className="section-heading">
          <p className="section-kicker">横向对比</p>
          <h4>目标产品与核心竞品对比</h4>
        </div>
      }
    >
      <div className="profile-comparison-matrix" role="table" aria-label="目标产品与核心竞品对比矩阵">
        <div className="profile-comparison-matrix-header" role="row">
          <div className="profile-comparison-corner" role="columnheader">
            <strong>对比维度</strong>
            <small>状态、风险与依据在每行统一说明。</small>
          </div>
          {PROFILE_COMPARISON_SLOT_ORDER.map((slot, index) => (
            <ProfileComparisonProductHeader
              key={slot}
              product={visibleProducts[index]}
              slot={slot}
            />
          ))}
        </div>
        <div className="profile-comparison-matrix-body" role="rowgroup">
          {(comparison.dimensions ?? []).map((dimension) => (
            <ProfileComparisonMatrixRow
              dimension={dimension}
              key={dimension.dimension_key}
              products={visibleProducts}
              taskId={taskId}
            />
          ))}
        </div>
      </div>
    </Card>
  );
}

function ProfileComparisonProductHeader({
  product,
  slot
}: {
  product: ProfileComparisonProduct | null;
  slot: ProfileComparisonSlot;
}) {
  const isEmpty = !product;

  return (
    <div
      className={
        isEmpty ? "profile-comparison-product-header is-empty" : "profile-comparison-product-header"
      }
      role="columnheader"
    >
      <ProfileComparisonImage product={product} slot={slot} />
      <div>
        <p>{PROFILE_COMPARISON_SLOT_LABELS[slot]}</p>
        <h5>{product?.product_name ?? PROFILE_COMPARISON_EMPTY_LABELS[slot]}</h5>
        {product ? <small>{formatNullable(product.brand)}</small> : <small>未发现可靠关系</small>}
      </div>
    </div>
  );
}

function ProfileComparisonMatrixRow({
  dimension,
  products,
  taskId
}: {
  dimension: ProfileComparisonDimension;
  products: Array<ProfileComparisonProduct | null>;
  taskId: string;
}) {
  const valuesByProduct = new Map(
    (dimension.values ?? []).map((value) => [value.product_id, value.value])
  );
  const evidenceIds = dimension.evidence_ids ?? [];

  return (
    <article className="profile-comparison-matrix-row" role="row">
      <div className="profile-comparison-dimension-cell" role="rowheader">
        <div className="profile-comparison-dimension-title">
          <Text strong>{dimension.dimension_label}</Text>
          <StatusBadge
            className={`profile-status-pill profile-status-${dimension.target_status}`}
            label={PROFILE_COMPARISON_STATUS_LABELS[dimension.target_status]}
          />
        </div>
        <p className="profile-comparison-status-reason">{dimension.status_reason}</p>
        <div className="profile-comparison-row-meta">
          <RiskFlagList riskFlags={dimension.risk_flags ?? []} />
          <Button
            onClick={() =>
              navigateTo(
                routePathForTask("/trace", taskId, {
                  evidence_id: evidenceIds[0],
                  tab: "evidence"
                })
              )
            }
            size="small"
            type="default"
          >
            查看依据
          </Button>
        </div>
      </div>
      {PROFILE_COMPARISON_SLOT_ORDER.map((slot, index) => {
        const product = products[index];
        const value = product
          ? (valuesByProduct.get(product.product_id) ?? EMPTY_VALUE_TEXT)
          : EMPTY_VALUE_TEXT;

        return (
          <div
            className={product ? "profile-comparison-value-cell" : "profile-comparison-value-cell is-empty"}
            data-slot-label={PROFILE_COMPARISON_SLOT_LABELS[slot]}
            key={`${dimension.dimension_key}-${slot}`}
            role="cell"
          >
            <p>{value}</p>
          </div>
        );
      })}
    </article>
  );
}

function ProfileComparisonImage({
  product,
  slot
}: {
  product: ProfileComparisonProduct | null;
  slot: ProfileComparisonSlot;
}) {
  const [hasImageError, setHasImageError] = useState(false);
  const imagePath = resolveBackendAssetUrl(product?.primary_image_path);

  if (!product || !imagePath || hasImageError) {
    return (
      <div
        className="profile-comparison-image profile-comparison-image-missing"
        role="img"
        aria-label={product ? "暂无可靠图片" : PROFILE_COMPARISON_EMPTY_LABELS[slot]}
      >
        {product ? "暂无可靠图片" : "暂无竞品"}
      </div>
    );
  }

  return (
    <div className="profile-comparison-image">
      <img
        alt={`${product.product_name} 缩略图`}
        onError={() => setHasImageError(true)}
        src={imagePath}
      />
    </div>
  );
}

function ProductBasicsCard({ profile }: { profile: ProductProfileData }) {
  const product = profile.product;

  return (
    <Card
      bordered={false}
      className="profile-panel profile-card-fill"
      title={
        <Space>
          <Zap size={18} />
          <div className="section-heading">
            <p className="section-kicker">目标产品</p>
            <h4>基础信息</h4>
          </div>
        </Space>
      }
    >
      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label="SKU 名称">{product.name}</Descriptions.Item>
        <Descriptions.Item label="品牌">{formatNullable(product.brand)}</Descriptions.Item>
        <Descriptions.Item label="店铺">{formatNullable(product.shop_name)}</Descriptions.Item>
        <Descriptions.Item label="品类">{product.category}</Descriptions.Item>
        <Descriptions.Item label="子类">{product.subcategory}</Descriptions.Item>
        <Descriptions.Item label="商品链接">{formatNullable(product.product_url)}</Descriptions.Item>
      </Descriptions>
      <TagList items={product.tags ?? []} emptyText="暂无标签" />
    </Card>
  );
}

function FeatureTreeCard({ profile }: { profile: ProductProfileData }) {
  const featureTree = profile.feature_tree;

  return (
    <Card
      bordered={false}
      className="profile-panel profile-card-fill"
      title={
        <Space>
          <Layers size={18} />
          <div className="section-heading">
            <p className="section-kicker">能力拆解</p>
            <h4>功能能力树</h4>
          </div>
        </Space>
      }
    >
      <div className="feature-grid">
        <ProfileFeatureList
          insight="这部分判断目标产品能否减少日常铲屎和清理负担，是自动猫砂盆最核心的购买理由。"
          items={featureTree.cleaning_capability ?? []}
          title="清洁能力"
        />
        <ProfileFeatureList
          insight="这部分关注气味管理是否有明确证据支撑；如果没有可靠来源，页面会保守显示为待补证。"
          items={featureTree.odor_control ?? []}
          title="除臭能力"
        />
        <ProfileFeatureList
          insight="这部分涉及宠物安全和电器安全，必须有更谨慎的证据边界，不能把宣传语直接写成确定事实。"
          items={featureTree.safety_features ?? []}
          title="安全能力"
        />
        <ProfileFeatureList
          insight="这部分说明产品是否能通过可视化、电动控制或自动化体验降低用户操作成本。"
          items={featureTree.smart_features ?? []}
          title="智能能力"
        />
        <ProfileFeatureList
          insight="这部分用于判断长期使用是否省心，包括耗材、清洁频率、套装和后续复核成本。"
          items={featureTree.maintenance_cost ?? []}
          title="维护成本"
        />
      </div>
      <RiskFlagList riskFlags={featureTree.risk_flags ?? []} />
    </Card>
  );
}

function ProfileFeatureList({
  insight,
  items,
  title
}: {
  insight: string;
  items: string[];
  title: string;
}) {
  const translatedItems = items.map(formatDisplayText).filter(Boolean);

  return (
    <section className="feature-list profile-feature-list">
      <h5>{title}</h5>
      <p>{insight}</p>
      {translatedItems.length > 0 ? (
        <ul>
          {translatedItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="muted-copy">暂无可靠数据，建议补充商品页截图、参数说明或评论证据后再下结论。</p>
      )}
    </section>
  );
}

function PricingModelCard({ profile }: { profile: ProductProfileData }) {
  const pricing = profile.pricing_model;
  const pricingEvidence = profile.pricing_evidence;
  const hasAccessTime =
    pricingEvidence.access_time_status === "available" && pricingEvidence.access_time;
  const promotions = pricing.promotions ?? [];

  return (
    <Card
      bordered={false}
      className="profile-panel profile-card-fill"
      title={
        <Space>
          <DollarSign size={18} />
          <div className="section-heading">
            <p className="section-kicker">价格模型</p>
            <h4>价格与证据</h4>
          </div>
        </Space>
      }
    >
      <Row gutter={[14, 14]} className="profile-price-metrics">
        <Col xs={24} sm={8}>
          <Text type="secondary">价格带</Text>
          <strong>{pricing.price_band || EMPTY_VALUE_TEXT}</strong>
        </Col>
        <Col xs={24} sm={8}>
          <Text type="secondary">标价</Text>
          <strong>{formatPrice(pricing.list_price, pricing.currency)}</strong>
        </Col>
        <Col xs={24} sm={8}>
          <Text type="secondary">到手价</Text>
          <strong>{formatPrice(pricing.final_price, pricing.currency)}</strong>
        </Col>
      </Row>
      <Descriptions column={1} size="small">
        <Descriptions.Item label="套装">{formatNullable(pricing.bundle_description)}</Descriptions.Item>
        <Descriptions.Item label="优惠信息">
          {promotions.length > 0 ? promotions.join("，") : EMPTY_VALUE_TEXT}
        </Descriptions.Item>
      </Descriptions>
      <div className={hasAccessTime ? "evidence-status" : "evidence-status evidence-status-risk"}>
        价格证据：
        {hasAccessTime
          ? formatDateTime(pricingEvidence.access_time, {
              emptyText: EMPTY_VALUE_TEXT,
              fallback: formatDisplayText
            })
          : EMPTY_VALUE_TEXT}
      </div>
      <RiskFlagList riskFlags={pricingEvidence.risk_flags ?? pricing.risk_flags ?? []} />
    </Card>
  );
}

function UserPersonaCard({ profile }: { profile: ProductProfileData }) {
  const persona = profile.user_persona;

  return (
    <Card
      bordered={false}
      className="profile-panel profile-card-fill"
      title={
        <Space>
          <Users size={18} />
          <div className="section-heading">
            <p className="section-kicker">用户理解</p>
            <h4>用户人群画像</h4>
          </div>
        </Space>
      }
    >
      {persona.is_inference ? (
        <Alert message="人群画像含推断内容，已保留推断标记。" type="warning" showIcon />
      ) : (
        <Alert message="人群画像来自直接证据。" type="success" showIcon />
      )}
      <div className="feature-grid profile-persona-grid">
        <FeatureList title="目标人群" items={persona.personas ?? []} />
        <FeatureList title="痛点" items={persona.pain_points ?? []} />
        <FeatureList title="使用场景" items={persona.scenarios ?? []} />
        <FeatureList title="决策因素" items={persona.decision_factors ?? []} />
      </div>
      <RiskFlagList riskFlags={persona.risk_flags ?? []} />
    </Card>
  );
}

function EvidenceSummaryCard({ profile }: { profile: ProductProfileData }) {
  return (
    <Card
      bordered={false}
      className="profile-panel profile-panel-wide"
      title={
        <div className="section-heading">
          <p className="section-kicker">证据摘要</p>
          <h4>证据摘要</h4>
        </div>
      }
    >
      <List
        className="profile-evidence-list"
        dataSource={profile.evidence_summaries ?? []}
        renderItem={(evidence, index) => (
          <List.Item key={evidence.evidence_id}>
            <EvidenceCard
              accessTime={evidence.access_time}
              accessTimeStatus={evidence.access_time_status}
              body={
                <div className="evidence-paragraphs">
                  {buildEvidenceParagraphs(evidence.content_summary, evidence.limitations).map(
                    (paragraph, paragraphIndex) => (
                      <p key={paragraphIndex}>{paragraph}</p>
                    )
                  )}
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="访问时间">
                      {evidence.access_time_status === "available"
                        ? formatDateTime(evidence.access_time, {
                            emptyText: EMPTY_VALUE_TEXT,
                            fallback: formatDisplayText
                          })
                        : EMPTY_VALUE_TEXT}
                    </Descriptions.Item>
                  </Descriptions>
                  <RiskFlagList riskFlags={evidence.risk_flags ?? []} />
                </div>
              }
              confidenceLevel={evidence.confidence_level}
              emptyText={EMPTY_VALUE_TEXT}
              formatText={formatDisplayText}
              riskFlags={evidence.risk_flags ?? []}
              sourceType={evidence.source_type}
              title={`证据 ${index + 1}`}
            />
          </List.Item>
        )}
      />
    </Card>
  );
}

function HumanReviewDrawer({
  apiClient,
  onClose,
  onSubmitted,
  open,
  profile,
  taskId
}: {
  apiClient: TaskApiClient;
  onClose: () => void;
  onSubmitted: () => void;
  open: boolean;
  profile: ProductProfileData;
  taskId: string;
}) {
  const [form] = Form.useForm<HumanReviewFormValues>();
  const [submitState, setSubmitState] =
    useState<ApiRequestState<HumanFeedbackCreateResponse>>(createIdleState());
  const reviewOptions = useMemo(() => buildHumanReviewOptions(profile), [profile]);
  const selectedFieldKey = Form.useWatch("fieldKey", form);
  const selectedOption = reviewOptions.find(
    (option) => option.key === (selectedFieldKey ?? reviewOptions[0]?.key)
  );
  const feedbackMutation = useMutation({
    mutationFn: (values: HumanReviewFormValues) => {
      const option = reviewOptions.find((item) => item.key === values.fieldKey);
      if (!option) {
        throw new Error("请选择修正字段。");
      }
      const payload: HumanFeedbackCreateRequest = {
        action: "update_field",
        after_value: {
          field: option.field,
          value: option.isList ? splitListValue(values.value) : values.value.trim()
        },
        reason: values.reason.trim(),
        target_id: option.targetId,
        target_type: option.targetType
      };
      return apiClient.post<HumanFeedbackCreateResponse>(
        `/tasks/${encodeURIComponent(taskId)}/feedback`,
        payload
      );
    },
    onError: (error) => {
      setSubmitState(createErrorState(error));
    },
    onSuccess: (data) => {
      setSubmitState({
        canRetry: false,
        data,
        error: null,
        retryCount: 0,
        status: "success"
      });
      form.setFieldsValue({ reason: "", value: "" });
      onSubmitted();
    }
  });

  useEffect(() => {
    const defaultKey = reviewOptions[0]?.key;
    if (defaultKey && !reviewOptions.some((option) => option.key === selectedFieldKey)) {
      form.setFieldValue("fieldKey", defaultKey);
    }
  }, [form, reviewOptions, selectedFieldKey]);

  return (
    <Drawer
      destroyOnHidden
      onClose={onClose}
      open={open}
      placement="right"
      title="受控人工修正"
      width="min(440px, 100vw)"
    >
      <aside aria-label="修正画像" className="human-review-panel human-review-drawer-panel">
        <div className="section-heading">
          <p className="section-kicker">受控复核</p>
          <h4>修正画像</h4>
        </div>
        <Alert
          message="合规提示"
          description="仅允许修正画像结构化字段；修改会被记录到 Trace 差异记录中。"
          showIcon
          type="info"
        />
        <div className="review-action-strip" aria-label="可用人工复核动作">
          <span>修正画像</span>
          <span>标记不采纳</span>
          <span>补充证据备注</span>
        </div>

        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => {
            setSubmitState(createIdleState());
            feedbackMutation.mutate(values);
          }}
        >
          <Form.Item
            initialValue={reviewOptions[0]?.key}
            label="画像字段"
            name="fieldKey"
            rules={[{ message: "请选择修正字段。", required: true }]}
          >
            <Select
              options={reviewOptions.map((option) => ({
                label: option.label,
                value: option.key
              }))}
              onChange={() => {
                form.setFieldsValue({ value: "" });
                setSubmitState(createIdleState());
              }}
            />
          </Form.Item>

          <Form.Item
            label="修正后的值"
            name="value"
            rules={[{ message: "请输入修正值。", required: true }]}
          >
            <Input.TextArea
              placeholder={
                selectedOption ? formatReviewValue(selectedOption.currentValue) : undefined
              }
              rows={4}
            />
          </Form.Item>

          <Form.Item
            label="修正原因"
            name="reason"
            rules={[{ message: "请输入修正理由。", required: true }]}
          >
            <Input.TextArea rows={3} />
          </Form.Item>

          {submitState.status === "error" ? (
            <RequestStateMessage className="review-error" state={submitState} />
          ) : null}
          {submitState.status === "success" ? (
            <div className="review-success" role="status">
              修正画像已提交，相关结果已刷新。
            </div>
          ) : null}

          <Button block htmlType="submit" loading={feedbackMutation.isPending} type="primary">
            提交修正画像
          </Button>
        </Form>
      </aside>
    </Drawer>
  );
}

function FeatureList({ items, title }: { items: string[]; title: string }) {
  return (
    <section className="feature-list">
      <h5>{title}</h5>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>{EMPTY_VALUE_TEXT}</p>
      )}
    </section>
  );
}

function TagList({ emptyText, items }: { emptyText: string; items: string[] }) {
  return (
    <div className="tag-list">
      {items.length > 0 ? (
        items.map((item) => <span key={item}>{item}</span>)
      ) : (
        <span>{emptyText}</span>
      )}
    </div>
  );
}

function buildHumanReviewOptions(profile: ProductProfileData): HumanReviewOption[] {
  return [
    {
      currentValue: profile.product.brand,
      field: "brand",
      key: "product.brand",
      label: "品牌",
      targetId: profile.product.product_id,
      targetType: "product"
    },
    {
      currentValue: profile.product.shop_name,
      field: "shop_name",
      key: "product.shop_name",
      label: "店铺",
      targetId: profile.product.product_id,
      targetType: "product"
    },
    {
      currentValue: profile.product.product_url,
      field: "product_url",
      key: "product.product_url",
      label: "商品链接",
      targetId: profile.product.product_id,
      targetType: "product"
    },
    {
      currentValue: profile.product.tags,
      field: "tags",
      isList: true,
      key: "product.tags",
      label: "产品标签",
      targetId: profile.product.product_id,
      targetType: "product"
    },
    {
      currentValue: profile.feature_tree.cleaning_capability,
      field: "cleaning_capability",
      isList: true,
      key: "feature.cleaning_capability",
      label: "清洁能力",
      targetId: profile.feature_tree.feature_tree_id,
      targetType: "feature_tree"
    },
    {
      currentValue: profile.feature_tree.odor_control,
      field: "odor_control",
      isList: true,
      key: "feature.odor_control",
      label: "除臭能力",
      targetId: profile.feature_tree.feature_tree_id,
      targetType: "feature_tree"
    },
    {
      currentValue: profile.feature_tree.safety_features,
      field: "safety_features",
      isList: true,
      key: "feature.safety_features",
      label: "安全能力",
      targetId: profile.feature_tree.feature_tree_id,
      targetType: "feature_tree"
    },
    {
      currentValue: profile.pricing_model.price_band,
      field: "price_band",
      key: "pricing.price_band",
      label: "价格带",
      targetId: profile.pricing_model.pricing_model_id,
      targetType: "pricing_model"
    },
    {
      currentValue: profile.pricing_model.promotions,
      field: "promotions",
      isList: true,
      key: "pricing.promotions",
      label: "优惠信息",
      targetId: profile.pricing_model.pricing_model_id,
      targetType: "pricing_model"
    },
    {
      currentValue: profile.pricing_model.bundle_description,
      field: "bundle_description",
      key: "pricing.bundle_description",
      label: "套装说明",
      targetId: profile.pricing_model.pricing_model_id,
      targetType: "pricing_model"
    },
    {
      currentValue: profile.user_persona.personas,
      field: "personas",
      isList: true,
      key: "persona.personas",
      label: "目标人群",
      targetId: profile.user_persona.persona_id,
      targetType: "user_persona"
    },
    {
      currentValue: profile.user_persona.pain_points,
      field: "pain_points",
      isList: true,
      key: "persona.pain_points",
      label: "痛点",
      targetId: profile.user_persona.persona_id,
      targetType: "user_persona"
    },
    {
      currentValue: profile.user_persona.scenarios,
      field: "scenarios",
      isList: true,
      key: "persona.scenarios",
      label: "使用场景",
      targetId: profile.user_persona.persona_id,
      targetType: "user_persona"
    },
    {
      currentValue: profile.user_persona.decision_factors,
      field: "decision_factors",
      isList: true,
      key: "persona.decision_factors",
      label: "决策因素",
      targetId: profile.user_persona.persona_id,
      targetType: "user_persona"
    }
  ];
}

function createTargetOnlyProfileComparison(profile: ProductProfileData): ProductProfileComparison {
  const evidenceIds = profile.product.evidence_ids ?? [];
  return {
    compared_products: [
      {
        brand: profile.product.brand,
        primary_image_path: profile.product.primary_image_path,
        product_id: profile.product.product_id,
        product_name: profile.product.name,
        product_url: profile.product.product_url,
        slot: "target"
      }
    ],
    dimensions: [
      {
        dimension_key: "price_band",
        dimension_label: "价格带",
        evidence_ids: profile.pricing_model.evidence_ids ?? evidenceIds,
        risk_flags: profile.pricing_model.risk_flags ?? [],
        status_reason: "仅有目标产品画像，竞品对比需要等待关系筛选结果。",
        target_status: "insufficient_evidence",
        trace_refs: [`profile:${profile.task_id}:price_band`],
        values: [
          {
            evidence_ids: profile.pricing_model.evidence_ids ?? evidenceIds,
            product_id: profile.product.product_id,
            value: profile.pricing_model.price_band || EMPTY_VALUE_TEXT
          }
        ]
      },
      {
        dimension_key: "core_selling_points",
        dimension_label: "核心卖点",
        evidence_ids: profile.feature_tree.evidence_ids ?? evidenceIds,
        risk_flags: profile.feature_tree.risk_flags ?? [],
        status_reason: "仅展示目标产品卖点，缺少竞品侧结构化对比。",
        target_status: "insufficient_evidence",
        trace_refs: [`profile:${profile.task_id}:core_selling_points`],
        values: [
          {
            evidence_ids: profile.feature_tree.evidence_ids ?? evidenceIds,
            product_id: profile.product.product_id,
            value:
              [
                ...(profile.feature_tree.cleaning_capability ?? []),
                ...(profile.feature_tree.odor_control ?? []),
                ...(profile.feature_tree.safety_features ?? []),
                ...(profile.feature_tree.smart_features ?? [])
              ]
                .slice(0, 4)
                .join("、") || EMPTY_VALUE_TEXT
          }
        ]
      },
      {
        dimension_key: "persona",
        dimension_label: "主要人群",
        evidence_ids: profile.user_persona.evidence_ids ?? evidenceIds,
        risk_flags: profile.user_persona.risk_flags ?? [],
        status_reason: "人群画像来自目标产品证据，竞品人群对照暂不可用。",
        target_status: "insufficient_evidence",
        trace_refs: [`profile:${profile.task_id}:persona`],
        values: [
          {
            evidence_ids: profile.user_persona.evidence_ids ?? evidenceIds,
            product_id: profile.product.product_id,
            value: (profile.user_persona.personas ?? []).join("、") || EMPTY_VALUE_TEXT
          }
        ]
      },
      {
        dimension_key: "scenario",
        dimension_label: "使用场景",
        evidence_ids: profile.user_persona.evidence_ids ?? evidenceIds,
        risk_flags: profile.user_persona.risk_flags ?? [],
        status_reason: "使用场景来自目标产品画像，竞品场景对照暂不可用。",
        target_status: "insufficient_evidence",
        trace_refs: [`profile:${profile.task_id}:scenario`],
        values: [
          {
            evidence_ids: profile.user_persona.evidence_ids ?? evidenceIds,
            product_id: profile.product.product_id,
            value: (profile.user_persona.scenarios ?? []).join("、") || EMPTY_VALUE_TEXT
          }
        ]
      },
      {
        dimension_key: "evidence_credibility",
        dimension_label: "证据可信状态",
        evidence_ids: evidenceIds,
        risk_flags: profile.pricing_evidence.risk_flags ?? [],
        status_reason: "未获得竞品横向证据，当前仅能查看目标产品证据状态。",
        target_status: "insufficient_evidence",
        trace_refs: [`profile:${profile.task_id}:evidence_credibility`],
        values: [
          {
            evidence_ids: evidenceIds,
            product_id: profile.product.product_id,
            value:
              profile.pricing_evidence.access_time_status === "available" ? "谨慎参考" : "证据不足"
          }
        ]
      }
    ],
    target_product_id: profile.product.product_id
  };
}

function splitListValue(value: string) {
  return value
    .split(/[\n,，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatReviewValue(value: HumanReviewOption["currentValue"]) {
  if (Array.isArray(value)) {
    return value.length > 0 ? value.join("，") : EMPTY_VALUE_TEXT;
  }

  return formatNullable(value);
}

function buildEvidenceParagraphs(
  summary: string | null | undefined,
  limitations?: string | null | undefined
) {
  const paragraphs: string[] = [];
  const summaryText = summary ? formatDisplayText(summary) : "";
  const summaryParts = summaryText
    .split(/；|;\s*/)
    .map(cleanEvidenceDisplayText)
    .filter(Boolean);

  for (const part of summaryParts) {
    if (isInternalEvidenceProcessText(part)) {
      continue;
    }

    let text = part
      .replace(/\s*本地快照[:：]\s*/g, "。商品与价格：")
      .replace(/^核心卖点[:：]\s*/g, "核心卖点：")
      .replace(/^评论摘要[:：]\s*/g, "评论与市场信号：")
      .replace(/^评论洞察/g, "评论洞察")
      .replace(/\bCNY\b/g, "元")
      .trim();

    if (!/[。！？]$/.test(text)) {
      text = `${text}。`;
    }

    paragraphs.push(text);
  }

  const limitationText = limitations ? cleanEvidenceDisplayText(formatDisplayText(limitations)) : "";
  if (limitationText && !isInternalEvidenceProcessText(limitationText)) {
    paragraphs.push(
      `证据边界：${/[。！？]$/.test(limitationText) ? limitationText : `${limitationText}。`}`
    );
  }

  return paragraphs.length > 0 ? paragraphs : [EMPTY_VALUE_TEXT];
}

function cleanEvidenceDisplayText(value: string) {
  return value
    .replace(/\[REDACTED\]/gi, "")
    .replace(/【REDACTED】/gi, "")
    .replace(/（REDACTED）/gi, "")
    .replace(/\(REDACTED\)/gi, "")
    .replace(/，\s*。/g, "。")
    .replace(/,\s*。/g, "。")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[，,；;]\s*$/g, "")
    .trim();
}

function isInternalEvidenceProcessText(value: string) {
  return /评论洞察尚待后续结构化抽取|QA\s*打回后补齐字段|补齐字段[:：]\s*source\.access_time|Evidence\.access_time|source\.access_time/i.test(
    value
  );
}

function formatDisplayText(value: string) {
  return formatReportText(value)
    .replace(/\bautomatic\b/g, "自动清理")
    .replace(/\bdemo_snapshot\b/g, "本地演示快照")
    .replace(/\bsmart_pet_hardware\b/g, "智能宠物硬件")
    .replace(/\bautomatic_litter_box\b/g, "自动猫砂盆")
    .replace(/\btarget\b/g, "目标产品");
}

function formatReportText(value: string) {
  return sanitizeTraceText(value)
    .replace(/\bProduct\b/g, "产品")
    .replace(/\bEvidence\b/g, "证据")
    .replace(/\bClaim\b/g, "分析判断")
    .replace(/\bCompetitionEdge\b/g, "竞争关系")
    .replace(/\bFeatureTree\b/g, "功能能力树")
    .replace(/\bPricingModel\b/g, "价格模型")
    .replace(/\bUserPersona\b/g, "用户人群画像")
    .replace(/\bdirect\b/g, "直接竞品")
    .replace(/\balternative\b/g, "需求替代")
    .replace(/\bchannel\b/g, "渠道替代")
    .replace(/\bclear_judgment\b/g, "判断较明确")
    .replace(/\bmedium\b/g, "中等可信度")
    .replace(/\bmissing_access_time\b/g, "缺少访问时间")
    .replace(/\bmissing_screenshot\b/g, "缺少截图")
    .replace(/\bcompleted\b/g, "已完成")
    .replace(/\bdemo_snapshot\b/g, "本地演示快照")
    .replace(/\bdouyin_sku_snapshot\b/g, "抖音商品快照")
    .replace(/\bCNY\b/g, "元")
    .replace(/\bprod_sku_\d+\b/g, "相关产品")
    .replace(/\bedge_[A-Za-z0-9_]+\b/g, "相关竞争关系")
    .replace(/\bclaim_[A-Za-z0-9_]+\b/g, "相关结论")
    .replace(/\bev_[A-Za-z0-9_]+\b/g, "相关证据");
}

function toQueryRequestState<TData>(query: {
  data?: TData;
  error: Error | null;
  isError: boolean;
  isFetching: boolean;
  isPending: boolean;
}): ApiRequestState<TData> {
  if (query.isPending || (query.isFetching && !query.data)) {
    return {
      canRetry: false,
      data: null,
      error: null,
      retryCount: 0,
      status: "loading"
    };
  }

  if (query.isError) {
    return createErrorState(query.error);
  }

  if (query.data) {
    return {
      canRetry: false,
      data: query.data,
      error: null,
      retryCount: 0,
      status: "success"
    };
  }

  return createIdleState();
}
