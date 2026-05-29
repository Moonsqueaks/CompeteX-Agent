import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import openapiTS, { astToString } from "../frontend/node_modules/openapi-typescript/dist/index.mjs";

const rootDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const schemaPath = resolve(rootDir, "frontend/src/api/schema.ts");
const bundledPython = resolve(rootDir, "backend/.conda312/python.exe");
const pythonExecutable = process.env.PYTHON ?? (existsSync(bundledPython) ? bundledPython : "python");

const openApiSchema = loadOpenApiSchema();
const nodes = await openapiTS(openApiSchema, {
  alphabetize: true,
  exportType: true
});

const generated = astToString(nodes);
const header = [
  "/**",
  " * This file is generated from the FastAPI OpenAPI schema.",
  " * Run `npm --prefix frontend run sync:types` after backend API contract changes.",
  " */",
  ""
].join("\n");

mkdirSync(dirname(schemaPath), { recursive: true });
writeFileSync(schemaPath, `${header}${generated}`, "utf8");
formatGeneratedSchema();

function loadOpenApiSchema() {
  const command = [
    "import json, sys",
    "sys.path.insert(0, 'backend')",
    "from app.main import create_app",
    "print(json.dumps(create_app().openapi(), ensure_ascii=False))"
  ].join("; ");

  const result = spawnSync(pythonExecutable, ["-c", command], {
    cwd: rootDir,
    encoding: "utf8"
  });

  if (result.status !== 0) {
    throw new Error(
      [
        `OpenAPI 导出失败，Python 命令退出码 ${result.status ?? "unknown"}。`,
        result.stderr.trim(),
        result.stdout.trim()
      ]
        .filter(Boolean)
        .join("\n")
    );
  }

  try {
    return JSON.parse(result.stdout);
  } catch (error) {
    throw new Error(
      `OpenAPI 导出结果不是有效 JSON：${error instanceof Error ? error.message : String(error)}`
    );
  }
}

function formatGeneratedSchema() {
  const result = spawnSync(
    process.execPath,
    [resolve(rootDir, "frontend/node_modules/prettier/bin/prettier.cjs"), "--write", schemaPath],
    {
      cwd: rootDir,
      encoding: "utf8"
    }
  );

  if (result.status !== 0) {
    throw new Error(
      [
        `OpenAPI 类型格式化失败，Prettier 退出码 ${result.status ?? "unknown"}。`,
        result.error?.message,
        result.stderr?.trim(),
        result.stdout?.trim()
      ]
        .filter(Boolean)
        .join("\n")
    );
  }
}
