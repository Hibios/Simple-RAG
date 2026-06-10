import collections.abc
import traceback
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.v1.endpoints.health import router as health_router
from api.v1.endpoints.rag import router as rag_router
from core.config import settings
from core.database import init_db
from core.exceptions import BaseAppError
from core.structlog_logs import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> collections.abc.AsyncGenerator[None, None]:
    setup_logging()
    logger.info("Starting up microservice...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down microservice...")


app: FastAPI = FastAPI(
    title=settings.get("PROJECT_NAME", "QnA RAG Service"),
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: collections.abc.Callable[
            [Request], collections.abc.Awaitable[Response]
        ],
    ) -> Response:
        response: Response = await call_next(request)
        logger.info(
            "HTTP Request processed",
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        )
        return response

app.add_middleware(LoggingMiddleware)

@app.exception_handler(BaseAppError)
async def app_error_handler(request: Request, exc: BaseAppError) -> JSONResponse:
    logger.error(
        "Application error caught",
        method=request.method,
        endpoint=request.url.path,
        message=exc.message,
        status_code=exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "ApplicationError", "details": exc.message},
    )


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    tb_lines = traceback.format_exc()
    logger.critical(
        "Critical unhandled exception caught",
        method=request.method,
        endpoint=request.url.path,
        error=str(exc),
        traceback=tb_lines,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "details": "An unexpected error occurred on the server.",
        },
    )


app.include_router(rag_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.UVICORN_HOST,
        port=settings.UVICORN_PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL,
        workers=settings.WORKERS,
    )
