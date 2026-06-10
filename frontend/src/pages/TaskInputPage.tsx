import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  Input,
  Radio,
  Row,
  Select,
  Space,
  Tag,
  Typography
} from "antd";
import { AlertTriangle, ArrowRight, FileText, Info, Rocket } from "lucide-react";

import { navigateTo, routePathForTask, type AppRoute } from "../app/routes";
import {
  ApiClientError,
  RequestStateMessage,
  createErrorState,
  createIdleState,
  createLoadingState
} from "../api";
import type { ApiClient, ApiRequestState, components } from "../api";
import { TASK_STATUS_LABELS } from "../domain/labels";
import { formatDateTime } from "../utils/format";

const { Paragraph, Text } = Typography;

type TaskApiClient = Pick<ApiClient, "get" | "post">;
type DataSourceMode = components["schemas"]["DataSourceMode"];
type EvidenceSourceMode = components["schemas"]["EvidenceSourceMode"];
type CandidateStrategy = components["schemas"]["CandidateStrategy"];
type TaskCreateRequest = components["schemas"]["TaskCreateRequest"];
type TaskCreateResponse = components["schemas"]["TaskCreateResponse"];
type TaskStatus = components["schemas"]["TaskStatus"];
type TaskStatusResponse = components["schemas"]["TaskStatusResponse"];

type TaskInputForm = {
  category: string;
  candidate_strategy: CandidateStrategy;
  evidence_source_mode: EvidenceSourceMode;
  research_text?: string;
  subcategory: string;
  target_product_name?: string;
  target_product_url: string;
};

const DEMO_PROFILES = {
  aiAssistant: {
    boundaryItems: [
      "当前 Demo 库支持豆包、Kimi、DeepSeek、千问、腾讯元宝等 AI 助手候选产品。",
      "定价、下载量、模型能力、用户规模和隐私安全结论必须有证据，缺失处会保守显示。"
    ],
    category: "互联网产品",
    candidateStrategy: "builtin_candidates" as CandidateStrategy,
    defaultTargetName: "豆包 Doubao",
    defaultTargetUrl: "https://www.doubao.com/chat/",
    evidenceSourceMode: "local_snapshot" as EvidenceSourceMode,
    subcategory: "AI 助手"
  },
  smartLitterBox: {
    boundaryItems: [
      "当前 Demo 库支持自动猫砂盆类目的 10+ 核心 SKU 识别。",
      "价格、图片、销量等数据已脱敏，非实时线上真实价格。"
    ],
    category: "smart_pet_hardware",
    candidateStrategy: "snapshot_pool" as CandidateStrategy,
    defaultTargetName: "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
    defaultTargetUrl: "https://v.douyin.com/mv8e4KRLLwc/",
    evidenceSourceMode: "local_snapshot" as EvidenceSourceMode,
    subcategory: "automatic_litter_box"
  }
} as const;

const DEFAULT_TASK_FORM: TaskInputForm = {
  category: DEMO_PROFILES.smartLitterBox.category,
  candidate_strategy: DEMO_PROFILES.smartLitterBox.candidateStrategy,
  evidence_source_mode: DEMO_PROFILES.smartLitterBox.evidenceSourceMode,
  research_text: "",
  subcategory: DEMO_PROFILES.smartLitterBox.subcategory,
  target_product_name: "",
  target_product_url: DEMO_PROFILES.smartLitterBox.defaultTargetUrl
};
const CATEGORY_OPTIONS = [
  { label: "智能宠物硬件", value: DEMO_PROFILES.smartLitterBox.category },
  { label: "互联网产品", value: DEMO_PROFILES.aiAssistant.category }
];
const SUBCATEGORY_OPTIONS_BY_CATEGORY: Record<string, { label: string; value: string }[]> = {
  [DEMO_PROFILES.aiAssistant.category]: [
    { label: DEMO_PROFILES.aiAssistant.subcategory, value: DEMO_PROFILES.aiAssistant.subcategory }
  ],
  [DEMO_PROFILES.smartLitterBox.category]: [
    {
      label: "自动猫砂盆",
      value: DEMO_PROFILES.smartLitterBox.subcategory
    }
  ]
};

export function TaskInputPage({
  apiClient,
  route,
  taskId
}: {
  apiClient: TaskApiClient;
  route: AppRoute;
  taskId: string | null;
}) {
  if (taskId) {
    return <CurrentTaskLanding apiClient={apiClient} route={route} taskId={taskId} />;
  }

  return <NewTaskFormPage apiClient={apiClient} route={route} />;
}

function NewTaskFormPage({ apiClient, route }: { apiClient: TaskApiClient; route: AppRoute }) {
  const [form] = Form.useForm<TaskInputForm>();
  const [currentCategory, setCurrentCategory] = useState(DEFAULT_TASK_FORM.category);
  const [currentCandidateStrategy, setCurrentCandidateStrategy] = useState<CandidateStrategy>(
    DEFAULT_TASK_FORM.candidate_strategy
  );
  const [currentEvidenceSourceMode, setCurrentEvidenceSourceMode] = useState<EvidenceSourceMode>(
    DEFAULT_TASK_FORM.evidence_source_mode
  );
  const [submissionState, setSubmissionState] =
    useState<ApiRequestState<TaskCreateResponse>>(createIdleState());
  const currentProfile =
    currentCategory === DEMO_PROFILES.aiAssistant.category
      ? DEMO_PROFILES.aiAssistant
      : DEMO_PROFILES.smartLitterBox;
  const createMutation = useMutation({
    mutationFn: (values: TaskInputForm) => createTaskWithSplitModeFallback(apiClient, values),
    onError: (error) => {
      setSubmissionState(createErrorState(error));
    },
    onSuccess: (response) => {
      setSubmissionState({
        canRetry: false,
        data: response,
        error: null,
        retryCount: 0,
        status: "success"
      });
      navigateTo(`/overview?task_id=${encodeURIComponent(response.task_id)}`);
    }
  });

  const handleCategoryChange = (category: string) => {
    const nextProfile =
      category === DEMO_PROFILES.aiAssistant.category
        ? DEMO_PROFILES.aiAssistant
        : DEMO_PROFILES.smartLitterBox;
    setCurrentCategory(category);
    setCurrentCandidateStrategy(nextProfile.candidateStrategy);
    setCurrentEvidenceSourceMode(nextProfile.evidenceSourceMode);
    form.setFieldsValue({
      category,
      candidate_strategy: nextProfile.candidateStrategy,
      evidence_source_mode: nextProfile.evidenceSourceMode,
      subcategory: nextProfile.subcategory,
      target_product_name: "",
      target_product_url: nextProfile.defaultTargetUrl
    });
  };

  return (
    <section className="page-surface task-input-modern-page" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">Demo 任务</p>
        <h3 id="page-title">{route.title}</h3>
        <p>{route.summary}</p>
      </div>

      <Row className="task-hub-layout" gutter={[24, 24]} align="stretch">
        <Col xs={24} lg={15}>
          <Card
            bordered={false}
            className="task-hub-card"
            title={
              <Space>
                <Rocket size={18} />
                创建分析任务
              </Space>
            }
          >
            <Form
              form={form}
              initialValues={DEFAULT_TASK_FORM}
              layout="vertical"
              onFinishFailed={() => {
                setSubmissionState(createIdleState());
              }}
              onFinish={(values) => {
                setSubmissionState(createIdleState());
                createMutation.mutate(values);
              }}
              requiredMark={false}
              size="large"
            >
              <Form.Item label="目标产品名称（选填）" name="target_product_name">
                <Input placeholder="可不填；系统会优先按链接匹配本地快照或候选池目标" />
              </Form.Item>

              <Form.Item
                label="目标产品链接"
                name="target_product_url"
                rules={[
                  {
                    validator: (_, value: string | undefined) =>
                      value?.trim()
                        ? Promise.resolve()
                        : Promise.reject(new Error("请输入目标产品链接。"))
                  }
                ]}
              >
                <Input placeholder="粘贴商品链接或产品官网入口；系统会用它匹配本地候选池" />
              </Form.Item>

              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="品类"
                    name="category"
                    rules={[{ message: "请选择品类。", required: true }]}
                  >
                    <Select onChange={handleCategoryChange} options={CATEGORY_OPTIONS} />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="子类"
                    name="subcategory"
                    rules={[{ message: "请选择子类。", required: true }]}
                  >
                    <Select options={SUBCATEGORY_OPTIONS_BY_CATEGORY[currentCategory]} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="候选竞品范围" name="candidate_strategy">
                <Radio.Group
                  className="task-mode-radio-group"
                  onChange={(event) =>
                    setCurrentCandidateStrategy(event.target.value as CandidateStrategy)
                  }
                >
                  <Space direction="vertical" size="small" style={{ width: "100%" }}>
                    <Radio value="snapshot_pool">
                      <span className="task-mode-label">
                        <strong>当前快照产品池</strong>
                        <small>直接使用当前领域快照里的产品集合。</small>
                      </span>
                    </Radio>
                    <Radio value="builtin_candidates">
                      <span className="task-mode-label">
                        <strong>领域内置候选池</strong>
                        <small>只输入目标，系统按领域自动带出候选。</small>
                      </span>
                    </Radio>
                  </Space>
                </Radio.Group>
              </Form.Item>

              <Form.Item label="证据来源" name="evidence_source_mode">
                <Radio.Group
                  className="task-mode-radio-group"
                  onChange={(event) =>
                    setCurrentEvidenceSourceMode(event.target.value as EvidenceSourceMode)
                  }
                >
                  <Space direction="vertical" size="small" style={{ width: "100%" }}>
                    <Radio value="local_snapshot">
                      <span className="task-mode-label">
                        <strong>仅本地快照</strong>
                        <small>使用脱敏快照、截图、评论摘要和用户研究文本。</small>
                      </span>
                    </Radio>
                    <Radio value="snapshot_plus_known_public_page">
                      <span className="task-mode-label">
                        <strong>本地快照 + 已知公开页补证</strong>
                        <small>访问已知公开 URL 补齐证据；失败时保留本地快照。</small>
                      </span>
                    </Radio>
                  </Space>
                </Radio.Group>
              </Form.Item>

              <Alert
                className="task-mode-alert"
                description="候选范围决定分析谁；证据来源决定用什么材料证明。"
                icon={<Info size={18} />}
                message="字段说明"
                showIcon
                type="info"
              />

              {currentEvidenceSourceMode === "snapshot_plus_known_public_page" ? (
                <Alert
                  className="task-mode-alert"
                  description="系统只尝试访问任务输入和本地快照已有的公开 URL，不绕过登录或验证码，也不搜索新竞品；页面不可用时自动降级为本地快照。"
                  icon={<AlertTriangle size={18} />}
                  message="稳定性提示"
                  showIcon
                  type="warning"
                />
              ) : null}
              {currentCandidateStrategy === "builtin_candidates" ? (
                <Alert
                  className="task-mode-alert"
                  description={
                    currentProfile === DEMO_PROFILES.aiAssistant
                      ? "系统会自动加载 AI 助手内置候选池：Kimi、DeepSeek、千问、腾讯元宝。候选只代表待分析对象，最终结论仍需 Evidence、Analysis 和 QA 支撑。"
                      : "系统会从本地脱敏 SKU 快照自动带出同池候选，候选只代表待分析对象，不等于确定竞品结论。"
                  }
                  icon={<Info size={18} />}
                  message="候选池提示"
                  showIcon
                  type="info"
                />
              ) : null}

              <Form.Item label="用户研究文本" name="research_text">
                <Input.TextArea
                  placeholder="可粘贴访谈记录或问卷结论，系统会提取需求、痛点和决策因素。"
                  rows={5}
                />
              </Form.Item>

              <Button
                block
                className="task-submit-button"
                htmlType="submit"
                loading={createMutation.isPending}
                type="primary"
              >
                {createMutation.isPending ? "创建中" : "启动分析任务"}
              </Button>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={9}>
          <Space className="task-hub-side" direction="vertical" size="middle">
            {submissionState.status === "error" ? (
              <RequestStateMessage className="submission-state" state={submissionState} />
            ) : null}

            <Alert
              description={
                <div>
                  <Paragraph>
                    系统将调用 4 类 Agent（采集、分析、质检、报告），围绕目标产品自动构建竞争图谱。
                  </Paragraph>
                  <Paragraph style={{ marginBottom: 0 }}>
                    任务创建后将进入竞争态势总览，可继续查看图谱、画像、报告和过程追踪。
                  </Paragraph>
                </div>
              }
              icon={<Info size={20} />}
              message="关于本次任务"
              showIcon
              type="info"
            />

            <Card bordered={false} className="task-hub-status-card" size="small">
              <Space align="start" size="middle">
                <FileText size={18} />
                <div>
                  <Text strong>演示数据边界</Text>
                  <ul>
                    {currentProfile.boundaryItems.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </Space>
            </Card>

            <Card bordered={false} className="task-hub-status-card" size="small">
              <dl className="summary-list">
                <div>
                  <dt>默认目标</dt>
                  <dd>{currentProfile.defaultTargetName}</dd>
                </div>
                <div>
                  <dt>提交后页面</dt>
                  <dd>竞争态势总览</dd>
                </div>
                <div>
                  <dt>候选范围</dt>
                  <dd>{candidateStrategyLabel(currentCandidateStrategy)}</dd>
                </div>
                <div>
                  <dt>证据来源</dt>
                  <dd>{evidenceSourceModeLabel(currentEvidenceSourceMode)}</dd>
                </div>
              </dl>
            </Card>
          </Space>
        </Col>
      </Row>
    </section>
  );
}

function CurrentTaskLanding({
  apiClient,
  route,
  taskId
}: {
  apiClient: TaskApiClient;
  route: AppRoute;
  taskId: string;
}) {
  const taskQuery = useQuery({
    enabled: Boolean(taskId),
    queryFn: () => apiClient.get<TaskStatusResponse>(`/tasks/${encodeURIComponent(taskId)}`),
    queryKey: ["task-input-current-task", taskId],
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && isTerminalTaskStatus(status) ? false : 2000;
    }
  });
  const task = taskQuery.data ?? null;
  const statusLabel = task ? (TASK_STATUS_LABELS[task.status] ?? task.status) : "正在读取";
  const isCompleted = task ? isAnalysisCompleted(task.status) : false;

  return (
    <section className="page-surface task-input-modern-page" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">当前任务</p>
        <h3 id="page-title">{route.title}</h3>
        <p>
          当前已经处在一个分析任务中。可以继续查看分析结果，也可以返回创建入口开始新的分析流程。
        </p>
      </div>

      <Card
        className="task-current-card"
        title={
          <Space>
            <FileText size={18} />
            当前分析任务
          </Space>
        }
      >
        <RequestStateMessage
          className="submission-state"
          loadingText="正在读取当前任务"
          onRetry={() => void taskQuery.refetch()}
          state={
            taskQuery.isPending
              ? createLoadingState()
              : taskQuery.isError
                ? createErrorState(taskQuery.error)
                : createIdleState<TaskStatusResponse>()
          }
        />

        {task ? (
          <Space className="task-current-content" orientation="vertical" size={18}>
            <div className="task-current-heading">
              <div>
                <Text type="secondary">目标产品</Text>
                <h4>{task.target_product_name}</h4>
              </div>
              <Tag color={isCompleted ? "green" : "blue"}>{statusLabel}</Tag>
            </div>

            <Row gutter={[12, 12]}>
              <Col xs={24} md={8}>
                <Card size="small">
                  <Text type="secondary">创建时间</Text>
                  <strong>{formatDateTime(task.created_at)}</strong>
                </Card>
              </Col>
              <Col xs={24} md={8}>
                <Card size="small">
                  <Text type="secondary">更新时间</Text>
                  <strong>{formatDateTime(task.updated_at)}</strong>
                </Card>
              </Col>
              <Col xs={24} md={8}>
                <Card size="small">
                  <Text type="secondary">候选范围</Text>
                  <strong>{candidateStrategyLabel(task.candidate_strategy)}</strong>
                </Card>
              </Col>
              <Col xs={24} md={8}>
                <Card size="small">
                  <Text type="secondary">证据来源</Text>
                  <strong>{evidenceSourceModeLabel(task.evidence_source_mode)}</strong>
                </Card>
              </Col>
            </Row>

            <Alert
              description={
                isCompleted
                  ? "当前任务已经完成。左侧 2-5 页面会继续展示同一份分析结果，不会重新启动分析。"
                  : "当前任务还在运行或等待处理。可以先查看总览或过程追踪，页面会根据任务状态继续刷新。"
              }
              showIcon
              message={isCompleted ? "分析已完成" : "分析任务进行中"}
              type={isCompleted ? "success" : "info"}
            />

            <Space wrap>
              <Button
                icon={<ArrowRight size={16} />}
                iconPlacement="end"
                onClick={() => navigateTo(routePathForTask("/overview", taskId))}
                type="primary"
              >
                继续查看总览
              </Button>
              <Button onClick={() => navigateTo(routePathForTask("/profile", taskId))}>
                查看产品画像
              </Button>
              <Button onClick={() => navigateTo(routePathForTask("/battlefield", taskId))}>
                查看竞争图谱
              </Button>
              <Button onClick={() => navigateTo(routePathForTask("/report", taskId))}>
                查看分析报告
              </Button>
              <Button onClick={() => navigateTo(routePathForTask("/trace", taskId))}>
                查看过程追踪
              </Button>
              <Button danger onClick={() => navigateTo("/")}>
                创建新的分析任务
              </Button>
            </Space>
          </Space>
        ) : null}
      </Card>
    </section>
  );
}

function isTerminalTaskStatus(status: TaskStatus) {
  return ["completed", "failed", "human_reviewing"].includes(status);
}

function isAnalysisCompleted(status: TaskStatus) {
  return status === "completed" || status === "human_reviewing";
}

function legacyDataSourceMode(form: TaskInputForm): DataSourceMode {
  if (form.evidence_source_mode === "snapshot_plus_known_public_page") {
    return "snapshot_plus_live";
  }
  if (form.candidate_strategy === "builtin_candidates") {
    return "builtin_candidates";
  }
  return "demo_snapshot";
}

function candidateStrategyLabel(strategy: CandidateStrategy) {
  return (
    {
      builtin_candidates: "领域内置候选池",
      snapshot_pool: "当前快照产品池"
    } satisfies Record<CandidateStrategy, string>
  )[strategy];
}

function evidenceSourceModeLabel(mode: EvidenceSourceMode) {
  return (
    {
      local_snapshot: "仅本地快照",
      snapshot_plus_known_public_page: "本地快照 + 已知公开页补证"
    } satisfies Record<EvidenceSourceMode, string>
  )[mode];
}

function toTaskCreateRequest(form: TaskInputForm): TaskCreateRequest {
  return {
    candidate_strategy: form.candidate_strategy,
    category: form.category.trim(),
    data_source_mode: legacyDataSourceMode(form),
    evidence_source_mode: form.evidence_source_mode,
    research_text: normalizeOptionalText(form.research_text ?? ""),
    subcategory: form.subcategory.trim(),
    target_product_name: normalizeOptionalText(form.target_product_name ?? ""),
    target_product_url: form.target_product_url.trim()
  };
}

async function createTaskWithSplitModeFallback(apiClient: TaskApiClient, values: TaskInputForm) {
  const request = toTaskCreateRequest(values);
  try {
    return await apiClient.post<TaskCreateResponse>("/tasks", request);
  } catch (error) {
    if (!isLegacySplitFieldValidationError(error)) {
      throw error;
    }
    return apiClient.post<TaskCreateResponse>("/tasks", toLegacyTaskCreateRequest(request));
  }
}

function toLegacyTaskCreateRequest(request: TaskCreateRequest) {
  return {
    category: request.category,
    data_source_mode: request.data_source_mode,
    research_text: request.research_text,
    subcategory: request.subcategory,
    target_product_name: request.target_product_name,
    target_product_url: request.target_product_url
  };
}

function isLegacySplitFieldValidationError(error: unknown) {
  if (!(error instanceof ApiClientError) || error.code !== "VALIDATION_ERROR") {
    return false;
  }
  const errors = error.details.errors;
  if (!Array.isArray(errors)) {
    return false;
  }
  const rejectedFields = new Set<string>();
  for (const item of errors) {
    if (!item || typeof item !== "object") {
      continue;
    }
    const loc = "loc" in item ? item.loc : null;
    const type = "type" in item ? item.type : null;
    if (!Array.isArray(loc) || type !== "extra_forbidden") {
      continue;
    }
    const field = loc[loc.length - 1];
    if (typeof field === "string") {
      rejectedFields.add(field);
    }
  }
  return rejectedFields.has("candidate_strategy") || rejectedFields.has("evidence_source_mode");
}

function normalizeOptionalText(value: string) {
  const stripped = value.trim();
  return stripped.length > 0 ? stripped : null;
}
