"""FastAPI application entrypoint for AI Financial Research Analyst."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.errors import register_exception_handlers
from app.api.routes import router
from app.config import settings
from app.utils.logging import logger


def create_app() -> FastAPI:
    """Factory function to build and configure the FastAPI application."""
    app = FastAPI(
        title="AI Financial Research Analyst API",
        description=(
            "A modular financial intelligence API combining multi-source SEC EDGAR/market data ingestion, "
            "deterministic quantitative valuation reasoning, and structured AI investment research synthesis."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # 1. Configurable CORS Middleware
    logger.info(f"Configuring CORS with allowed origins: {settings.cors_allowed_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # 2. Centralized Error Handlers
    register_exception_handlers(app)

    # 3. Mount API Routes
    app.include_router(router)

    # 4. Root redirect to interactive documentation
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return RedirectResponse(url="/docs")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)