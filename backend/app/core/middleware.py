import time
import uuid
from fastapi import Request
from loguru import logger


async def request_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.time()

    logger.info(
        f"[{request_id}] {request.method} {request.url.path} started"
    )

    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)

    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"completed {response.status_code} in {duration}ms"
    )

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration}ms"
    return response
