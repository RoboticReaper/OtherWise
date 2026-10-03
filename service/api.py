"""Bounded authenticated API. No browser history or persistent profile storage."""

from __future__ import annotations

import asyncio
import hmac
import logging
import os
import threading
import time
import unicodedata
from collections import deque
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator
from starlette.concurrency import run_in_threadpool

from .engine import FocusIdentityConflict, RecommendationEngine, UnknownFocusTopic
from .discovery import DiscoveryEngine

MAX_BODY_BYTES = 16_384
REQUESTS_PER_MINUTE = 30
LOGGER = logging.getLogger("otherwise.service")
Phrase = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=120)]
UnitControl = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
GraphId = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=120)]


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    keywords: Annotated[list[Phrase], Field(min_length=1, max_length=40)]
    mode: Literal["path", "global"]
    focus: Phrase | None
    expansion_level: Annotated[int, Field(ge=0, le=8)]
    limit: Annotated[int, Field(ge=1, le=100)]
    radius: UnitControl = .28
    expansion: UnitControl = .07
    overlap: UnitControl = .015
    diversity: UnitControl = .20
    max_overlap_fraction: Annotated[float, Field(ge=0, le=.95, allow_inf_nan=False)] = .20
    randomness: UnitControl = .03

    @field_validator("keywords")
    @classmethod
    def clean_keywords(cls, values):
        return [cls.clean_phrase(value) for value in values]

    @field_validator("focus")
    @classmethod
    def clean_focus(cls, value):
        return cls.clean_phrase(value) if value is not None else None

    @staticmethod
    def clean_phrase(value):
        if any(unicodedata.category(char).startswith("C") for char in value):
            raise ValueError("Topic phrases cannot contain control characters.")
        value = value.strip()
        if not any(char.isalnum() for char in value):
            raise ValueError("Topic phrases must contain text.")
        return value

    @model_validator(mode="after")
    def approved_focus(self):
        if self.focus is not None and self.focus not in self.keywords:
            raise ValueError("Focus must be an approved keyword.")
        return self


class ConceptFeedback(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    concept_id: GraphId
    area_id: GraphId
    curious: bool
    known: bool
    difficulty: Literal['none', 'too_basic', 'too_hard']


class DiscoveryRequest(RecommendationRequest):
    feedback: Annotated[list[ConceptFeedback], Field(max_length=4000)] = Field(default_factory=list)
    exposures: Annotated[dict[GraphId, Annotated[int, Field(ge=0, le=1_000_000_000)]], Field(max_length=100)] = Field(default_factory=dict)
    seed: Annotated[int, Field(ge=0, le=2**31-1)] = 42
    exploration_fraction: UnitControl = .3


Digest = Annotated[str, StringConstraints(strict=True, pattern=r"^[0-9a-f]{64}$")]
IdentityText = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=200)]


class FocusEmbedding(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    sha256: Digest
    dtype: IdentityText
    shape: Annotated[list[Annotated[int, Field(ge=1)]], Field(min_length=2, max_length=2)]

    @field_validator("shape")
    @classmethod
    def mpnet_dimensions(cls, values):
        if values[1] != 768:
            raise ValueError("Invalid embedding dimensions.")
        return values


class FocusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    # Canonical IDs are preserved exactly, without phrase trimming or folding.
    topic_id: IdentityText
    catalog_sha256: Digest
    model: IdentityText
    embedding: FocusEmbedding
    limit: Annotated[int, Field(ge=1, le=100)] = 10
    radius: UnitControl = .28
    expansion: UnitControl = .07
    overlap: UnitControl = .015
    diversity: UnitControl = .20
    max_overlap_fraction: Annotated[float, Field(ge=0, le=.95, allow_inf_nan=False)] = .20
    randomness: UnitControl = .03


def error(detail, status, **headers):
    return JSONResponse({"detail": detail}, status_code=status, headers=headers)


class RequestBoundary:
    """Authenticate before parsing, bound streamed bodies, and rate-limit globally.

    The rate queue contains only monotonic timestamps. It is deliberately global
    for this shared-token single-worker demo, so no IP/profile keys are retained.
    """

    def __init__(self, app, *, token):
        self.app = app
        self.token = token.encode("utf-8") if token else None
        self.requests = deque()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] not in {"/api/recommend", "/api/focus", "/api/discover"} or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        authorization = headers.get(b"authorization", b"")
        supplied = authorization[7:] if authorization.startswith(b"Bearer ") else b""
        if not self.token or not hmac.compare_digest(supplied, self.token):
            return await error("A valid access token is required.", 401,
                               **{"WWW-Authenticate": "Bearer"})(scope, receive, send)
        now = time.monotonic()
        while self.requests and self.requests[0] <= now - 60:
            self.requests.popleft()
        if len(self.requests) >= REQUESTS_PER_MINUTE:
            return await error("Request limit reached. Try again shortly.", 429,
                               **{"Retry-After": "60"})(scope, receive, send)
        self.requests.append(now)
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await error("Invalid request.", 400)(scope, receive, send)
        max_bytes = 1_048_576 if scope['path'] == '/api/discover' else MAX_BODY_BYTES
        if declared > max_bytes:
            return await error("Request is too large.", 413)(scope, receive, send)
        body = bytearray()
        try:
            async with asyncio.timeout(10):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    if len(body) + len(chunk) > max_bytes:
                        return await error("Request is too large.", 413)(scope, receive, send)
                    body.extend(chunk)
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            return await error("Request timed out.", 408)(scope, receive, send)
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)


def create_app(engine=None, token=None, discovery_engine=None):
    default_engine = engine is None
    engine = engine if engine is not None else RecommendationEngine(device=os.getenv("OTHERWISE_MODEL_DEVICE") or None)
    if discovery_engine is None and default_engine:
        discovery_engine = DiscoveryEngine(engine)
    access_token = token if token is not None else os.getenv("OTHERWISE_API_TOKEN", "")
    compute = threading.BoundedSemaphore(1)

    @asynccontextmanager
    async def lifespan(app):
        app.state.ready = False
        app.state.discovery_ready = False
        try:
            await run_in_threadpool(engine.initialize)
            app.state.ready = bool(engine.ready)
            if discovery_engine is not None:
                try:
                    await run_in_threadpool(discovery_engine.initialize)
                    app.state.discovery_ready = bool(discovery_engine.ready)
                except Exception:
                    LOGGER.warning('Graph recommendation initialization failed.')
        except Exception:
            # Exception details can include input/model credentials; never log them.
            LOGGER.warning("Recommendation engine initialization failed.")
        yield
        app.state.ready = False

    app = FastAPI(title="OtherWise", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.ready = False

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Pydantic's default error contains input values; discard the entire tree.
        return error("Invalid recommendation request.", 422)

    @app.get("/health")
    def health():
        ready = bool(app.state.ready)
        return JSONResponse({"ready": ready}, status_code=200 if ready else 503)

    @app.post("/api/recommend")
    def recommendations(payload: RecommendationRequest):
        if not app.state.ready:
            return error("Recommendation service is unavailable.", 503)
        if not compute.acquire(blocking=False):
            return error("Recommendation service is busy. Try again shortly.", 429, **{"Retry-After": "2"})
        try:
            result = engine.recommend(payload.keywords, mode=payload.mode, focus=payload.focus,
                                      expansion_level=payload.expansion_level, limit=payload.limit,
                                      radius=payload.radius, expansion=payload.expansion,
                                      overlap=payload.overlap, diversity=payload.diversity,
                                      max_overlap_fraction=payload.max_overlap_fraction,
                                      randomness=payload.randomness)
            return {"recommendations": result, "mode": payload.mode, "expansion_level": payload.expansion_level}
        except Exception:
            LOGGER.warning("Recommendation computation failed.")
            return error("Recommendation service is unavailable. Try again shortly.", 503)
        finally:
            compute.release()

    @app.post("/api/focus")
    def focus_recommendations(payload: FocusRequest):
        if not app.state.ready:
            return error("Recommendation service is unavailable.", 503)
        if not compute.acquire(blocking=False):
            return error("Recommendation service is busy. Try again shortly.", 429, **{"Retry-After": "2"})
        try:
            return engine.recommend_focus(
                payload.topic_id,
                expected_identity=dict(catalog_sha256=payload.catalog_sha256, model=payload.model,
                                       embedding=payload.embedding.model_dump()),
                limit=payload.limit, radius=payload.radius, expansion=payload.expansion,
                overlap=payload.overlap, diversity=payload.diversity,
                max_overlap_fraction=payload.max_overlap_fraction, randomness=payload.randomness,
            )
        except FocusIdentityConflict:
            return error("Catalog source version conflict.", 409)
        except UnknownFocusTopic:
            return error("Invalid recommendation request.", 422)
        except Exception:
            LOGGER.warning("Recommendation computation failed.")
            return error("Recommendation service is unavailable. Try again shortly.", 503)
        finally:
            compute.release()

    @app.post('/api/discover')
    def specific_recommendations(payload: DiscoveryRequest):
        if not app.state.ready or not app.state.discovery_ready:
            return error('Recommendation service is unavailable.', 503)
        if not compute.acquire(blocking=False):
            return error('Recommendation service is busy. Try again shortly.', 429, **{'Retry-After': '2'})
        try:
            return discovery_engine.recommend(**payload.model_dump())
        except ValueError:
            return error('Invalid recommendation request.', 422)
        except Exception:
            LOGGER.warning('Graph recommendation computation failed.')
            return error('Recommendation service is unavailable. Try again shortly.', 503)
        finally:
            compute.release()

    app.add_middleware(RequestBoundary, token=access_token)
    origins = [item.strip() for item in os.getenv("OTHERWISE_CORS_ORIGINS", "").split(",") if item.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins,
                       allow_origin_regex=r"chrome-extension://[a-p]{32}",
                       allow_methods=["POST", "GET"], allow_headers=["Authorization", "Content-Type"])
    return app
