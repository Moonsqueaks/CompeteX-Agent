import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.responses import get_trace_id, register_api_response_handlers, success_response
from app.api.routes_battlefield import router as battlefield_router
from app.api.routes_feedback import router as feedback_router
from app.api.routes_profile import router as profile_router
from app.api.routes_reports import router as reports_router
from app.api.routes_tasks import router as tasks_router
from app.api.routes_trace import router as trace_router

LOCAL_DEV_CORS_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5174",
    "http://localhost:5174",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
)
LOCAL_DEV_CORS_ORIGIN_REGEX = r"^http://(127\.0\.0\.1|localhost):(41\d{2}|51\d{2})$"


def create_app(
    database_url: str | None = None,
    *,
    auto_start_task_execution: bool = False,
    report_output_dir: str | None = None,
    run_task_execution_inline: bool = False,
) -> FastAPI:
    app = FastAPI(title="Competitive Intelligence Agent System")
    app.state.database_url = database_url
    app.state.report_output_dir = report_output_dir or os.getenv("REPORT_OUTPUT_DIR")
    app.state.auto_start_task_execution = auto_start_task_execution
    app.state.run_task_execution_inline = run_task_execution_inline
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(LOCAL_DEV_CORS_ORIGINS),
        allow_origin_regex=LOCAL_DEV_CORS_ORIGIN_REGEX,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        allow_private_network=True,
    )
    register_api_response_handlers(app)
    app.include_router(tasks_router)
    app.include_router(profile_router)
    app.include_router(battlefield_router)
    app.include_router(reports_router)
    app.include_router(trace_router)
    app.include_router(feedback_router)

    @app.get("/health")
    def health_check(request: Request):
        return success_response({"status": "ok"}, get_trace_id(request))

    return app


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


app = create_app(
    auto_start_task_execution=True,
    run_task_execution_inline=_env_flag("RUN_TASK_EXECUTION_INLINE"),
)
