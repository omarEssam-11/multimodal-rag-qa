"""Multimodal RAG QA — FastAPI application entry point."""

from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager

# Windows: the default Proactor event loop aborts the whole server with
# "OSError: [WinError 64] The specified network name is no longer available"
# whenever a client (browser / Vite proxy) drops a keep-alive connection.
# The Selector loop tolerates those aborted accepts, so images and health
# checks keep serving instead of killing uvicorn.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import chat, documents, retrieve, system
from app.config import settings
from app.utils.logger import get_logger, set_request_id

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    logger.info("Starting %s (env=%s)", settings.app_name, settings.app_env)
    logger.info("Qdrant mode: %s", settings.qdrant_mode)
    logger.info("LLM provider: %s (%s)", settings.llm_provider, settings.llm_model)
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    description="CLIP-powered multimodal document QA with retrieval-augmented generation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or set_request_id()
    set_request_id(rid)
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


# API routers
app.include_router(system.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(retrieve.router)

# Serve extracted images (safe endpoint also exists at /api/images)
app.mount("/api/images", StaticFiles(directory=settings.extracted_images_dir), name="images")


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
    )
