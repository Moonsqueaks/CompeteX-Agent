from fastapi import FastAPI, Request

from app.api.responses import get_trace_id, register_api_response_handlers, success_response
from app.api.routes_battlefield import router as battlefield_router
from app.api.routes_feedback import router as feedback_router
from app.api.routes_profile import router as profile_router
from app.api.routes_reports import router as reports_router
from app.api.routes_tasks import router as tasks_router
from app.api.routes_trace import router as trace_router


def create_app(database_url: str | None = None) -> FastAPI:
    app = FastAPI(title="Competitive Intelligence Agent System")
    app.state.database_url = database_url
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


app = create_app()
