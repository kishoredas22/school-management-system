"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import AppException
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.utils.helpers import error_response, success_response

configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if settings.database_url.startswith("sqlite"):
            init_db()
        logger.info("application_started")
        yield

    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get(f"{settings.api_v1_prefix}/health")
    def health_check():
        return success_response(data={"status": "ok"}, message="Service healthy")

    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.message, exc.error_code, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content=error_response("Request validation failed", "VALIDATION_ERROR", {"errors": exc.errors()}),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "unhandled_exception",
            extra={"path": request.url.path, "method": request.method, "request_id": getattr(request.state, "request_id", None)},
        )
        return JSONResponse(
            status_code=500,
            content=error_response("Internal server error", "INTERNAL_SERVER_ERROR"),
        )

    return app


app = create_app()
