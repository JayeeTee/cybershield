"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from cybershield.api.auth import create_access_token, enforce_public_rate_limit
from cybershield.api.models import TokenRequest, TokenResponse
from cybershield.api.routes.dashboard import router as dashboard_router
from cybershield.api.routes.intel import router as intel_router
from cybershield.api.routes.scan import router as scan_router


def create_app() -> FastAPI:
    """Application factory for CyberShield REST API."""
    app = FastAPI(
        title="CyberShield API",
        description="Unified cybersecurity REST API for scans, threat intelligence, and dashboard insights.",
        version="0.1.0",
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                }
            },
        )

    @app.post("/api/v1/auth/token", response_model=TokenResponse, tags=["auth"])
    async def issue_token(credentials: TokenRequest, _: None = Depends(enforce_public_rate_limit)) -> TokenResponse:
        # Replace with identity provider validation in production.
        if credentials.password != "cybershield":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return create_access_token(subject=credentials.username)

    app.include_router(scan_router)
    app.include_router(intel_router)
    app.include_router(dashboard_router)
    return app


app = create_app()
