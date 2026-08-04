"""FastAPI entrypoint for the Intelligent Code Evaluation Assistant."""
import asyncio
import json
import os
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List

from bson import ObjectId
import env_loader  # noqa: F401
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agent import run_evaluation
from database import get_reviews_collection, lifespan
from schemas import ReviewRequest, ReviewResponse

load_dotenv(env_loader.ENV_PATH)

DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app = FastAPI(title="Intelligent Code Evaluation Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ensure_gemini_api_key() -> None:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key_here":
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured. Set a valid key in backend/.env and restart the API.",
        )


@app.get("/api/v1/health")
async def health() -> dict:
    return {"status": "ok"}


def _friendly_error(exc: Exception) -> str:
    """Turn provider SDK errors into something worth showing a user."""
    text = str(exc)
    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        return (
            "Gemini rate limit reached for this API key. Free-tier keys allow only a "
            "few requests per minute. Wait a minute and try again, or set a different "
            "GEMINI_MODEL in backend/.env."
        )
    if "NOT_FOUND" in text or "404" in text:
        return (
            "The configured GEMINI_MODEL is not available to this API key. "
            "Set GEMINI_MODEL=gemini-3.6-flash in backend/.env and restart the API."
        )
    if "UNAVAILABLE" in text or "503" in text:
        return "Gemini is temporarily overloaded. Please try again in a moment."
    if "PERMISSION_DENIED" in text or "API_KEY_INVALID" in text or "401" in text:
        return "Gemini rejected the API key. Check GEMINI_API_KEY in backend/.env."
    return f"Evaluation failed: {text}"


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    doc["strategy_plan"] = doc.get("strategy_plan") or []
    doc["findings"] = doc.get("findings") or []
    return doc


async def _store_review(payload: ReviewRequest, result: dict) -> ReviewResponse:
    doc = {
        "programming_language": payload.programming_language,
        "source_code": payload.source_code,
        "strategy_plan": result["strategy_plan"],
        "findings": result["findings"],
        "refactored_code": result["refactored_code"],
        "quality_score": result["quality_score"],
        "executive_summary": result["executive_summary"],
        "created_at": datetime.utcnow(),
    }
    insert = await get_reviews_collection().insert_one(doc)
    doc["_id"] = insert.inserted_id
    return ReviewResponse(**_serialize(doc))


@app.post("/api/v1/reviews", response_model=ReviewResponse)
async def create_review(payload: ReviewRequest) -> ReviewResponse:
    _ensure_gemini_api_key()
    try:
        result = await run_evaluation(payload.programming_language, payload.source_code)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_friendly_error(exc)) from exc
    return await _store_review(payload, result)


@app.post("/api/v1/reviews/stream")
async def create_review_stream(payload: ReviewRequest) -> StreamingResponse:
    """Same as POST /api/v1/reviews, but streams stage progress as NDJSON.

    Each line is one JSON event: {"stage": "analyzing"}, then "refactoring",
    "saving", and finally {"stage": "done", "review": {...}} or
    {"stage": "error", "detail": "..."}.
    """
    _ensure_gemini_api_key()
    queue: asyncio.Queue = asyncio.Queue()

    async def on_progress(event: Dict[str, Any]) -> None:
        await queue.put(event)

    async def run() -> None:
        try:
            result = await run_evaluation(
                payload.programming_language, payload.source_code, on_progress
            )
            await queue.put({"stage": "saving"})
            review = await _store_review(payload, result)
            await queue.put({"stage": "done", "review": jsonable_encoder(review)})
        except Exception as exc:  # surfaced to the client as an error event
            await queue.put({"stage": "error", "detail": _friendly_error(exc)})
        finally:
            await queue.put(None)

    async def events() -> AsyncGenerator[str, None]:
        task = asyncio.create_task(run())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield json.dumps(event) + "\n"
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    return StreamingResponse(
        events(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/v1/reviews", response_model=List[ReviewResponse])
async def list_reviews(limit: int = 20) -> List[ReviewResponse]:
    cursor = get_reviews_collection().find().sort("created_at", -1).limit(limit)
    return [ReviewResponse(**_serialize(doc)) async for doc in cursor]


@app.get("/api/v1/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: str) -> ReviewResponse:
    if not ObjectId.is_valid(review_id):
        raise HTTPException(status_code=400, detail="Invalid review id")
    doc = await get_reviews_collection().find_one({"_id": ObjectId(review_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse(**_serialize(doc))
