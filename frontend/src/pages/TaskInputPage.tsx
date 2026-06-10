import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Col, Form, Input, Radio, Row, Select, Space, Tag, Typography } from "antd";
import { AlertTriangle, ArrowRight, FileText, Info, Rocket } from "lucide-react";

import { navigateTo, routePathForTask, type AppRoute } from "../app/routes";
import { RequestStateMessage, createErrorState, createIdleState, createLoadingState } from "../api";
import type { ApiClient, ApiRequestState, components } from "../api";
import { TASK_STATUS_LABELS } from "../domain/labels";
import { formatDateTime } from "../utils/format";

const { Paragraph, Text } = Typography;

type TaskApiClient = Pick<ApiClient, "get" | "post">;
type DataSourceMode = components["schemas"]["DataSourceMode"];
type TaskCreateRequest = components["schemas"]["TaskCreateRequest"];
type TaskCreateResponse = components["schemas"]["TaskCreateResponse"];
type TaskStatus = components["schemas"]["TaskStatus"];
type TaskStatusResponse = components["schemas"]["TaskStatusResponse"];

type TaskInputForm = {
  category: string;
  data_source_mode: DataSourceMode;
  research_text?: string;
  subcategory: string;
  target_product_name?: string;
  target_product_url: string;
};

const DEFAULT_TASK_FORM: TaskInputForm = {
  category: "smart_pet_hardware",
  data_source_mode: "demo_snapshot",
  research_text: "",
  subcategory: "automatic_litter_box",
  target_product_name: "",
  target_product_url: "https://v.douyin.com/mv8e4KRLLwc/"
};
const DEFAULT_TARGET_NAME = "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆";
const CATEGORY_OPTIONS = [{ label: "智能宠物硬件", value: "smart_pet_hardware" }];
const SUBCATEGORY_OPTIONS = [{ label: "自动猫砂盆", value: "automatic_litter_box" }];

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

function NewTaskFormPage({
  apiClient,
  route
}: {
  apiClient: TaskApiClient;
  route: AppRoute;
}) {
  const [form] = Form.useForm<TaskInputForm>();
  const [currentMode, setCurrentMode] = useState<DataSourceMode>(DEFAULT_TASK_FORM.data_source_mode);
  const [submissionState, setSubmissionState] =
    useState<ApiRequestState<TaskCreateResponse>>(createIdleState());
  const createMutation = useMutation({
    mutationFn: (values: TaskInputForm) =>
      apiClient.post<TaskCreateResponse>("/tasks", toTaskCreateRequest(values)),
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
                <Input placeholder="可不填；系统会优先按商品链接匹配快照 SKU" />
              </Form.Item>

              <Form.Item
                label="商品链接"
                name="target_product_url"
                rules={[
                  {
                    validator: (_, value: string | undefined) =>
                      value?.trim()
                        ? Promise.resolve()
                        : Promise.reject(new Error("请输入商品链接。"))
                  }
                ]}
              >
                <Input placeholder="粘贴抖音商品链接；系统会用它匹配本地脱敏 SKU 快照" />
              </Form.Item>

              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="品类"
                    name="category"
                    rules={[{ message: "请选择品类。", required: true }]}
                  >
                    <Select options={CATEGORY_OPTIONS} />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="子类"
                    name="subcategory"
                    rules={[{ message: "请选择子类。", required: true }]}
                  >
                    <Select options={SUBCATEGORY_OPTIONS} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="数据模式" name="data_source_mode">
                <Radio.Group
                  className="task-mode-radio-group"
                  onChange={(event) => setCurrentMode(event.target.value as DataSourceMode)}
                >
                  <Space direction="vertical" size="small" style={{ width: "100%" }}>
                    <Radio value="demo_snapshot">
                      <span className="task-mode-label">
                        <strong>本地快照</strong>
                        <small>使用脱敏 SKU 快照运行稳定 Demo。</small>
                      </span>
                    </Radio>
                    <Radio value="snapshot_plus_live">
                      <span className="task-mode-label">
                        <strong>快照 + 公开页增强</strong>
                        <small>访问已知公开 URL 补齐证据；失败时保留本地快照。</small>
                      </span>
                    </Radio>
                  </Space>
                </Radio.Group>
              </Form.Item>

              {currentMode === "snapshot_plus_live" ? (
                <Alert
                  className="task-mode-alert"
                  description="系统只尝试访问任务输入和本地快照已有的公开 URL，不绕过登录或验证码，也不搜索新竞品；页面不可用时自动降级为本地快照。"
                  icon={<AlertTriangle size={18} />}
                  message="稳定性提示"
                  showIcon
                  type="warning"
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
                    <li>当前 Demo 库支持自动猫砂盆类目的 10+ 核心 SKU 识别。</li>
                    <li>价格、图片、销量等数据已脱敏，非实时线上真实价格。</li>
                  </ul>
                </div>
              </Space>
            </Card>

            <Card bordered={false} className="task-hub-status-card" size="small">
              <dl className="summary-list">
                <div>
                  <dt>默认目标</dt>
                  <dd>{DEFAULT_TARGET_NAME}</dd>
                </div>
                <div>
                  <dt>提交后页面</dt>
                  <dd>竞争态势总览</dd>
                </div>
                <div>
                  <dt>当前模式</dt>
                  <dd>{currentMode === "demo_snapshot" ? "本地快照" : "已知公开页增强"}</dd>
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
                  <Text type="secondary">数据模式</Text>
                  <strong>{task.data_source_mode === "snapshot_plus_live" ? "快照 + 公开页增强" : "本地快照"}</strong>
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
              title={isCompleted ? "分析已完成" : "分析任务进行中"}
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

function toTaskCreateRequest(form: TaskInputForm): TaskCreateRequest {
  return {
    category: form.category.trim(),
    data_source_mode: form.data_source_mode,
    research_text: normalizeOptionalText(form.research_text ?? ""),
    subcategory: form.subcategory.trim(),
    target_product_name: normalizeOptionalText(form.target_product_name ?? ""),
    target_product_url: form.target_product_url.trim()
  };
}

function normalizeOptionalText(value: string) {
  const stripped = value.trim();
  return stripped.length > 0 ? stripped : null;
}
