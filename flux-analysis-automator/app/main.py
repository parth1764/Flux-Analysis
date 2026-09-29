from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from app.api.routes import banks, dashboard, explanations, financials, flux, health, ingestion
from app.core.config import get_settings
from app.core.logging import setup_logging

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Automated month-end flux analysis: ingest public bank financials, "
            "calculate material variances, generate validated AI explanations, "
            "and expose Power BI-friendly APIs."
        ),
        lifespan=lifespan,
    )
    prefix = settings.api_prefix

    @app.get("/")
    def root():
        return {
            "service": "flux-analysis-automator",
            "version": "1.0.0",
            "docs": "/docs",
            "health": f"{prefix}/health",
            "dashboard_ui": "/ui",
            "dashboard": f"{prefix}/dashboard/summary",
        }

    @app.get("/json/version")
    def json_version():
        return {"version": "1.0.0"}

    @app.get("/ui")
    def dashboard_ui():
        return FileResponse(STATIC_DIR / "dashboard.html")

    app.include_router(health.router, prefix=prefix)
    app.include_router(banks.router, prefix=prefix)
    app.include_router(financials.router, prefix=prefix)
    app.include_router(flux.router, prefix=prefix)
    app.include_router(explanations.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
    app.include_router(ingestion.router, prefix=prefix)

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    return app


app = create_app()
