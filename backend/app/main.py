"""FastAPI app entrypoint: CORS, router mounting, startup DB init + seed."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text

from app.api.routers import (
    auth,
    bookings,
    chat,
    dashboard,
    lawyers,
    messages,
    payments,
    support,
)
from app.core.config import get_settings
from app.db.models import RevokedToken, utcnow
from app.db.seed import seed_if_empty
from app.db.session import Base, SessionLocal, engine
from app.services.errors import ServiceError

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # create_all never adds columns to an existing table; add the ones introduced since the
    # first release so an older dev database keeps working.
    if "brief_json" not in {c["name"] for c in inspect(engine).get_columns("bookings")}:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN brief_json TEXT"))
    db = SessionLocal()
    try:
        seed_if_empty(db)
        # Bound the revoked_tokens table without needing a cron job — see
        # docs/DECISIONS.md "Resolution pass with user, 2026-07-18" (#9).
        db.query(RevokedToken).filter(RevokedToken.expires_at < utcnow()).delete()
        db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="Nya-AI API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(ServiceError)
async def service_error(_: Request, exc: ServiceError) -> JSONResponse:
    """Services raise ServiceError subclasses; reply with the same shape as HTTPException."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(lawyers.router, prefix="/api")
app.include_router(bookings.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(support.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
