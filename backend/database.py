"""Async MongoDB connection using Motor."""
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import env_loader  # noqa: F401
from dotenv import load_dotenv
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

load_dotenv(env_loader.ENV_PATH)
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "code_reviewer_db")
client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None

async def connect_to_mongo() -> None:
    global client, db
    try:
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]
        await db.client.admin.command("ping")
        print(f"Successfully connected to MongoDB database: {DATABASE_NAME}")
    except Exception as exc:
        print(f"MongoDB connection failed: {exc}", file=sys.stderr)
        local = "localhost" in MONGODB_URL or "127.0.0.1" in MONGODB_URL
        hint = "Start local MongoDB (mongod or Windows MongoDB service)." if local else "Verify Atlas username/password and IP whitelist."
        print(f"Hint: {hint}", file=sys.stderr)
        raise

def get_db() -> AsyncIOMotorDatabase:
    if db is None:
        raise RuntimeError("Database not initialized")
    return db

def get_reviews_collection():
    return get_db()["reviews"]

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await connect_to_mongo()
    yield
    global client, db
    if client:
        client.close()
        client = None
        db = None
