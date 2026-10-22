import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from api.routers import routers
from core.models import init, close
from core.shared.errors import AppError
from core.shared.logger import configure_divine_logging, logger
from settings import settings

_request_log = logging.getLogger("api.request")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    The function `lifespan` in Python starts a scheduler, sets a webhook URL if it's different, runs the
    main function, and then deletes the webhook.

    Args:
        app (FastAPI): FastAPI instance representing the application.
    """
    configure_divine_logging()  # после старта uvicorn — перевешиваем логи на наш handler
    await main()
    yield
    await close()


async def main():
    """
    The main function initializes a bot with specified configurations, registers middlewares and
    handlers, and starts polling for updates.
    """

    await init()


app = FastAPI(
    lifespan=lifespan,
    openapi_url="/openapi.json",
    docs_url="/",
    default_response_class=ORJSONResponse,
)

for router in routers:
    app.include_router(router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return ORJSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", path=request.url.path, error=str(exc))
    return ORJSONResponse(status_code=500, content={"detail": str(exc)})


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логируем каждый входящий запрос — видно, доходит ли до приложения."""
    _request_log.info(
        "%s %s",
        request.method,
        request.url.path,
        extra={"method": request.method, "path": request.url.path},
    )
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
        # Add other trusted domains here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
