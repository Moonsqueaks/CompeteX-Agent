import { Layout, Menu, Space, Typography } from "antd";
import {
  ActivitySquare,
  FileOutput,
  GitCompare,
  ListTodo,
  Network,
  Route,
  SearchCheck
} from "lucide-react";
import { Outlet, useLocation, useNavigate } from "react-router";

import { getRoute, NAV_ROUTES } from "./routes";

const { Content, Sider } = Layout;
const { Text, Title } = Typography;

const WORKFLOW_ROUTES = [
  { icon: ListTodo, path: "/", step: "1" },
  { icon: ActivitySquare, path: "/overview", step: "2" },
  { icon: GitCompare, path: "/profile", step: "3" },
  { icon: Network, path: "/battlefield", step: "4" },
  { icon: FileOutput, path: "/report", step: "5" }
] as const;

const TRACE_ROUTE = { icon: SearchCheck, path: "/trace" } as const;

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const currentRoute = getRoute(location.pathname);

  const workflowMenuItems = WORKFLOW_ROUTES.map((workflowRoute) => {
    const route = getRoute(workflowRoute.path);
    const Icon = workflowRoute.icon;

    return {
      key: route.path,
      label: (
        <button
          aria-current={route.path === currentRoute.path ? "page" : undefined}
          aria-label={route.label}
          className="nav-item-button workflow-nav-button"
          type="button"
        >
          <span className="workflow-step-index" aria-hidden="true">
            [ {workflowRoute.step} ]
          </span>
          <Icon aria-hidden="true" size={16} />
          <span className="workflow-nav-copy">
            <span className="workflow-nav-title">{route.label}</span>
            <span className="workflow-nav-summary">{route.summary}</span>
          </span>
        </button>
      )
    };
  });

  const traceRoute = NAV_ROUTES.find((route) => route.path === TRACE_ROUTE.path);
  const traceMenuItems = traceRoute
    ? [
        {
          key: traceRoute.path,
          label: (
            <button
              aria-current={traceRoute.path === currentRoute.path ? "page" : undefined}
              aria-label={traceRoute.label}
              className="nav-item-button trace-nav-button"
              type="button"
            >
              <TRACE_ROUTE.icon aria-hidden="true" size={16} />
              <span>
                <span className="workflow-nav-title">{traceRoute.label}</span>
                <span className="workflow-nav-summary">独立查看证据链、质检和运行过程</span>
              </span>
            </button>
          )
        }
      ]
    : [];

  function handleMenuClick({ key }: { key: string }) {
    navigate(key === "/" ? key : `${key}${location.search}`);
  }

  return (
    <Layout className="workspace-shell">
      <Sider
        aria-label="主导航"
        className="workspace-sidebar"
        theme="light"
        width={280}
      >
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">竞析</span>
          <Space orientation="vertical" size={0}>
            <Text className="brand-kicker">竞析智能体</Text>
            <Title className="brand-title" level={1}>
              竞品关系重建系统
            </Title>
          </Space>
        </div>
        <div className="workflow-nav-heading">
          <Route aria-hidden="true" size={14} />
          <span>分析流水线</span>
        </div>
        <Menu
          className="workspace-nav"
          items={workflowMenuItems}
          mode="inline"
          onClick={handleMenuClick}
          selectedKeys={[currentRoute.path]}
        />
        <div className="trace-nav-section">
          <div className="workflow-nav-heading trace-nav-heading">
            <span>技术追踪</span>
          </div>
          <Menu
            className="workspace-nav trace-nav"
            items={traceMenuItems}
            mode="inline"
            onClick={handleMenuClick}
            selectedKeys={[currentRoute.path]}
          />
        </div>
      </Sider>
      <Layout className="workspace-main">
        <Content className="workspace-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
