"""FastAPI entrypoint for the Intelligent Code Evaluation Assistant."""
import os
from datetime import datetime
from typing import List

from bson import ObjectId
import env_loader  # noqa: F401
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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


def _ensure_openai_api_key() -> None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or key == "your_openai_api_key_here":
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured. Set a valid key in backend/.env and restart the API.",
        )


@app.get("/api/v1/health")
async def health() -> dict:
    return {"status": "ok"}


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    doc["strategy_plan"] = doc.get("strategy_plan") or []
    doc["findings"] = doc.get("findings") or []
    return doc


@app.post("/api/v1/reviews", response_model=ReviewResponse)
async def create_review(payload: ReviewRequest) -> ReviewResponse:
    _ensure_openai_api_key()
    try:
        result = await run_evaluation(payload.programming_language, payload.source_code)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Evaluation failed: {exc}") from exc
    doc = {
        "programming_language": payload.programming_language,        "source_code": payload.source_code,
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
