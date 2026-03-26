from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.core.database import check_db_connection
from app.core.logging import setup_logging
from app.core.middleware import request_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(f"Starting Mini-ERP | ENV={settings.APP_ENV}")
    db_ok = await check_db_connection()
    if not db_ok:
        logger.warning("Database not reachable at startup — check DATABASE_URL")
    else:
        logger.info("Database connected")
    yield
    # Shutdown
    logger.info("Mini-ERP shutting down")


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Mini-ERP Platform — HCM, Payroll, AP, Expenses, Procurement, GL",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    return await request_middleware(request, call_next)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ── Routers — uncomment as each module is built ───────────────────────────────
# from app.api.v1 import auth, workforce, payroll, accounts_payable
# from app.api.v1 import expenses, procurement, general_ledger, admin
# app.include_router(auth.router,             prefix="/api/v1/auth",        tags=["Auth"])
# app.include_router(workforce.router,        prefix="/api/v1/workforce",   tags=["Workforce"])
# app.include_router(payroll.router,          prefix="/api/v1/payroll",     tags=["Payroll"])
# app.include_router(accounts_payable.router, prefix="/api/v1/ap",          tags=["AP"])
# app.include_router(expenses.router,         prefix="/api/v1/expenses",    tags=["Expenses"])
# app.include_router(procurement.router,      prefix="/api/v1/procurement", tags=["Procurement"])
# app.include_router(general_ledger.router,   prefix="/api/v1/gl",          tags=["GL"])
# app.include_router(admin.router,            prefix="/api/v1/admin",       tags=["Admin"])


# ── Health + Info ─────────────────────────────────────────────────────────────
@app.get("/api/v1/health", tags=["System"], include_in_schema=False)
async def health_check():
    db_ok = await check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": "connected" if db_ok else "disconnected",
    }


@app.get("/api/v1/info", tags=["System"])
async def app_info():
    return {
        "title": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "modules": [
            "workforce", "payroll", "accounts_payable",
            "expenses", "procurement", "general_ledger",
        ],
    }
