from __future__ import annotations

import logging
import resource
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.ai import ai_router
from backend.config import settings
from backend.db import db
from backend.middleware import BoundedTokenBucket
from backend.models import CampaignCreate, ContributionCreate, GenerateRequest
from backend.services.ai import generate_concepts
from backend.services.campaigns import graduate, list_campaigns, refund
from backend.services.http import external_http
from backend.services.sources import source_status
from backend.services.trends import list_trends, scan_trends
from backend.solana.adapter import build_graduation_plan

logger = logging.getLogger("omnipool")
ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"

rate_limiter = BoundedTokenBucket(
    requests_per_minute=settings.rate_limit_per_minute,
    max_clients=settings.max_rate_limit_clients,
)


def _rss_megabytes() -> float:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return round(rss / divisor, 2)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init()
    await external_http.start()
    if settings.scan_on_startup:
        try:
            await scan_trends()
        except Exception:
            logger.warning("Initial trend scan failed", exc_info=True)

    try:
        yield
    finally:
        await external_http.close()


app = FastAPI(
    title="OMNIPOOL AI",
    version="0.3.0",
    lifespan=lifespan,
    docs_url="/api/docs",
)
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.middleware("http")
async def request_guardrails(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("x-request-id") or uuid4().hex

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            body_size = int(content_length)
        except ValueError:
            return JSONResponse(
                {"detail": "invalid_content_length", "request_id": request_id},
                status_code=400,
            )
        if body_size > settings.max_request_bytes:
            return JSONResponse(
                {"detail": "request_too_large", "request_id": request_id},
                status_code=413,
            )

    path = request.url.path
    if not path.startswith("/static") and path not in {"/", "/api/health", "/api/v1/health"}:
        client_key = request.client.host if request.client else "unknown"
        if not rate_limiter.allow(client_key):
            return JSONResponse(
                {"detail": "rate_limit_exceeded", "request_id": request_id},
                status_code=429,
                headers={"Retry-After": "1"},
            )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    latency_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "%s %s status=%s latency_ms=%.2f request_id=%s",
        request.method,
        path,
        response.status_code,
        latency_ms,
        request_id,
    )
    return response


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")


@app.get("/api/health")
@app.get("/api/v1/health")
def health() -> dict:
    return {
        "ok": True,
        "version": app.version,
        "env": settings.app_env,
        "rss_mb": _rss_megabytes(),
        "time": time.time(),
    }


@app.get("/api/trends")
@app.get("/api/v1/trends")
def trends(limit: int = 30) -> list[dict]:
    return list_trends(limit)


@app.get("/api/sources")
@app.get("/api/v1/sources")
def sources() -> list[dict]:
    return source_status()


@app.get("/api/ai/status")
@app.get("/api/v1/ai/status")
async def ai_status() -> list[dict]:
    health = await ai_router.health()
    return [item.model_dump() for item in health]


@app.post("/api/trends/scan")
@app.post("/api/v1/trends/scan")
async def scan() -> list[dict]:
    return await scan_trends()


@app.post("/api/generate")
@app.post("/api/v1/generate")
async def generate(req: GenerateRequest) -> list[dict]:
    trend = (
        db.row("SELECT * FROM trends WHERE id=?", (req.trend_id,))
        if req.trend_id
        else None
    )
    if not trend and req.title:
        trend = {
            "id": f"custom-{uuid4().hex}",
            "title": req.title,
            "summary": req.summary or req.title,
            "score": 75.0,
            "confidence": 50.0,
            "risk": 20.0,
            "novelty": 80.0,
            "saturation": 15.0,
            "risk_flags": "[]",
        }

    if not trend:
        raise HTTPException(404, "trend_not_found")

    try:
        return await generate_concepts(trend)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        logger.warning("Concept generation failed", exc_info=True)
        raise HTTPException(502, "generation_failed") from exc


@app.get("/api/campaigns")
@app.get("/api/v1/campaigns")
def campaigns() -> list[dict]:
    return list_campaigns()


@app.post("/api/campaigns")
@app.post("/api/v1/campaigns")
def create_campaign(req: CampaignCreate) -> dict:
    if not req.risk_acknowledged:
        raise HTTPException(400, "risk_acknowledgement_required")

    concept = db.row("SELECT * FROM concepts WHERE id=?", (req.concept_id,))
    if not concept:
        raise HTTPException(404, "concept_not_found")

    return db.create_campaign(
        concept,
        creator_wallet=req.creator_wallet,
        duration_minutes=req.duration_minutes,
    )


@app.post("/api/campaigns/{campaign_id}/contribute")
@app.post("/api/v1/campaigns/{campaign_id}/contribute")
def contribute(campaign_id: str, req: ContributionCreate) -> dict:
    try:
        return db.contribute(
            campaign_id,
            wallet=req.wallet,
            amount_sol=req.amount_sol,
            idempotency_key=req.idempotency_key,
        )
    except KeyError as exc:
        raise HTTPException(404, exc.args[0]) from exc
    except ValueError as exc:
        detail = str(exc)
        status = 422 if "amount" in detail or "lamport" in detail else 409
        raise HTTPException(status, detail) from exc


@app.post("/api/campaigns/{campaign_id}/graduate")
@app.post("/api/v1/campaigns/{campaign_id}/graduate")
def graduate_route(campaign_id: str) -> dict:
    try:
        campaign = graduate(campaign_id)
    except KeyError as exc:
        raise HTTPException(404, exc.args[0]) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

    return {
        "campaign": campaign,
        "plan": build_graduation_plan(campaign_id),
    }


@app.post("/api/campaigns/{campaign_id}/refund/{wallet}")
@app.post("/api/v1/campaigns/{campaign_id}/refund/{wallet}")
def refund_route(campaign_id: str, wallet: str) -> dict:
    try:
        return refund(campaign_id, wallet)
    except KeyError as exc:
        raise HTTPException(404, exc.args[0]) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
