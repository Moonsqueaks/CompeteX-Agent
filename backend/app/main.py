from fastapi import FastAPI, Request

from app.api.responses import get_trace_id, register_api_response_handlers, success_response


def create_app() -> FastAPI:
    app = FastAPI(title="Competitive Intelligence Agent System")
    register_api_response_handlers(app)

    @app.get("/health")
    def health_check(request: Request):
        return success_response({"status": "ok"}, get_trace_id(request))

    return app


app = create_app()
