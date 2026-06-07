export type AppRoute = {
  eyebrow: string;
  label: string;
  path: string;
  sections: string[];
  summary: string;
  title: string;
};

export const ROUTES: AppRoute[] = [
  {
    path: "/",
    label: "任务输入",
    title: "分析任务输入",
    eyebrow: "任务启动",
    summary: "创建自动猫砂盆分析任务，并确认本次演示使用的数据范围。",
    sections: ["目标产品", "数据模式", "研究文本"]
  },
  {
    path: "/overview",
    label: "竞争态势总览",
    title: "竞争态势总览",
    eyebrow: "决策工作台",
    summary: "围绕当前任务查看结论、状态、关键竞品和下钻入口。",
    sections: ["核心判断", "关键竞品", "行动建议", "证据风险"]
  },
  {
    path: "/profile",
    label: "产品与竞品画像",
    title: "产品与竞品画像",
    eyebrow: "横向画像",
    summary: "查看目标产品与核心竞品的基础信息、价格模型、人群和证据状态。",
    sections: ["目标产品", "核心竞品", "价格模型", "用户人群"]
  },
  {
    path: "/battlefield",
    label: "竞争图谱",
    title: "竞争关系图谱",
    eyebrow: "关系网络",
    summary: "按价格带、人群、场景、评分和证据覆盖查看竞争关系。",
    sections: ["切片控制", "关系图谱", "评分解释", "证据卡片"]
  },
  {
    path: "/report",
    label: "分析报告",
    title: "分析报告",
    eyebrow: "汇报输出",
    summary: "承载最终结论、质检摘要和证据索引的网页报告结构。",
    sections: ["结论摘要", "核心竞品拆解", "产品策略建议", "证据与质检附录"]
  },
  {
    path: "/trace",
    label: "证据与过程追踪",
    title: "证据与过程追踪",
    eyebrow: "证据链路",
    summary: "展示证据链、质检打回、运行记录、工具调用和差异记录。",
    sections: ["证据链", "质检记录", "运行记录", "差异记录"]
  }
];

export const NAV_ROUTES = ROUTES.filter((route) => route.path !== "/");

export function getRoute(pathname: string) {
  return ROUTES.find((route) => route.path === pathname) ?? ROUTES[0];
}

export function routePathForTask(
  path: string,
  taskId: string | null,
  query: Record<string, string | null | undefined> = {}
) {
  const params = new URLSearchParams();
  if (taskId && path !== "/") {
    params.set("task_id", taskId);
  }
  for (const [key, value] of Object.entries(query)) {
    if (value) {
      params.set(key, value);
    }
  }
  const queryString = params.toString();
  return queryString ? `${path}?${queryString}` : path;
}

export const navigationEmitter = new EventTarget();

export function navigateTo(path: string) {
  navigationEmitter.dispatchEvent(new CustomEvent("navigate", { detail: path }));
}
