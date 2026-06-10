import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Alert, Button, Card, Col, Form, Input, Radio, Row, Select, Space, Typography } from "antd";
import { AlertTriangle, FileText, Info, Rocket } from "lucide-react";

import { navigateTo, type AppRoute } from "../app/routes";
import { RequestStateMessage, createErrorState, createIdleState } from "../api";
import type { ApiClient, ApiRequestState, components } from "../api";

const { Paragraph, Text } = Typography;

type TaskApiClient = Pick<ApiClient, "get" | "post">;
type DataSourceMode = components["schemas"]["DataSourceMode"];
type TaskCreateRequest = components["schemas"]["TaskCreateRequest"];
type TaskCreateResponse = components["schemas"]["TaskCreateResponse"];

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
