from fastapi import FastAPI, Request

from app.api.responses import get_trace_id, register_api_response_handlers, success_response
from app.api.routes_tasks import router as tasks_router


def create_app(database_url: str | None = None) -> FastAPI:
    app = FastAPI(title="Competitive Intelligence Agent System")
    app.state.database_url = database_url
    register_api_response_handlers(app)
    app.include_router(tasks_router)

    @app.get("/health")
    def health_check(request: Request):
        return success_response({"status": "ok"}, get_trace_id(request))

    return app


app = create_app()
