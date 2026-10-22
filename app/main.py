import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import health_router, router
from app.core.config import get_settings
from app.core.errors import HTTP_ERROR, INTERNAL_ERROR, INVALID_INPUT
from app.db.session import Base, SessionLocal, engine
from app.services.payloads import cleanup_expired_transforms

settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    cleanup_task = (
        asyncio.create_task(_cleanup_loop()) if settings.cache_cleanup_interval_seconds else None
    )
    yield
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


async def _cleanup_loop() -> None:
    while True:
        await asyncio.sleep(settings.cache_cleanup_interval_seconds)
        try:
            with SessionLocal() as session:
                cleanup_expired_transforms(session)
        except Exception:
            logger.exception("Transform cache cleanup failed")


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(router, prefix=settings.api_prefix)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"loc": error["loc"], "msg": error["msg"], "type": error["type"]} for error in exc.errors()
    ]
    return JSONResponse(
        status_code=INVALID_INPUT.status_code,
        content={"error": INVALID_INPUT.code, "message": INVALID_INPUT.message, "details": details},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        content = exc.detail
    else:
        content = {"error": HTTP_ERROR.code, "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled request error", exc_info=exc)
    return JSONResponse(
        status_code=INTERNAL_ERROR.status_code,
        content={"error": INTERNAL_ERROR.code, "message": INTERNAL_ERROR.message},
    )
