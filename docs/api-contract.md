# API Contract Notes

This document records the current 2.0 frontend/backend contract. Paths are relative to the project root unless they are HTTP routes.

## Scope

The MVP uses FastAPI, SQLite, LangGraph, React, Vite, TanStack Query and React Flow. It does not introduce Celery, Redis, PostgreSQL, Next.js, Redux, Tailwind, external live collection, microservices or a PDF rendering service.

## Task Flow

1. `POST /tasks` creates an analysis task and starts the in-process workflow.
2. The frontend redirects new tasks to `/overview?task_id=<task_id>`.
3. While a task is running, the frontend polls `GET /tasks/{task_id}` and page-specific data endpoints.
4. Completed or human-reviewing tasks can read report, profile, battlefield, overview and trace data.

## Core Endpoints

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/tasks` | Create a task from target product input and optional research text. |
| `GET` | `/tasks/{task_id}` | Read task status for polling and refresh recovery. |
| `GET` | `/tasks/{task_id}/overview` | Read the 2.0 competitive situation overview. |
| `GET` | `/tasks/{task_id}/profile` | Read target and competitor profile data. |
| `GET` | `/tasks/{task_id}/battlefield` | Read competitive graph, slice options, key relations and evidence cards. |
| `GET` | `/tasks/{task_id}/report` | Read the web report `ReportData`. |
| `GET` | `/tasks/{task_id}/report/docx` | Download the official Word `.docx` report. |
| `GET` | `/tasks/{task_id}/trace` | Read evidence chains, quality records, DAG, process details and diffs. |
| `POST` | `/tasks/{task_id}/feedback` | Submit controlled Human Review changes. |

## Report Delivery

The formal 2.0 delivery format is the web report plus Word `.docx` export. Browser print or "save as PDF" is a frontend convenience and does not require a backend PDF service.

The frontend must not display a Markdown export button. `GET /tasks/{task_id}/report/markdown` is not a user-facing 2.0 endpoint and is covered by regression tests as unavailable.

Word export writes generated files and simplified relationship graph images under `data/reports/` by default. Export failure must not hide or invalidate the web report. Failure metadata stored in Trace must be diagnostic but must not include local output paths, raw exception text, API keys, tokens, phone numbers, account IDs or addresses.

## Trace Contract

`GET /tasks/{task_id}/trace` exposes four reader-facing groups:

1. Evidence chains grouped by Claim.
2. Quality records derived from QA review tasks.
3. Agent process data, including DAG nodes, DAG edges, run logs, tool calls, token usage and folded prompt previews.
4. Diff records for QA repair, analysis recompute and Human Review updates.

Prompt previews are summaries only. Raw prompts, secrets and long private research text must not be returned.

## Security Contract

All API responses, report data, Word export text, Trace data, export metadata and frontend page rendering must redact API keys, tokens, secrets, phone numbers, account IDs and addresses. Sensitive pet safety, electrical certification and medical or beauty claims must use conservative language or be flagged by QA.

Writer output is built from structured Product, Evidence, Claim, CompetitionEdge, ReviewTask and workflow metadata. Model polishing is optional only; if any future model enhancement conflicts with structured evidence or QA results, the structured evidence and QA result prevail.
