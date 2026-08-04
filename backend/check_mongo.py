"""Quick connectivity check for MongoDB using backend/.env settings."""
import asyncio
import sys

from database import MONGODB_URL, DATABASE_NAME, connect_to_mongo, client


async def main() -> int:
    try:
        await connect_to_mongo()
        print(f"OK: MongoDB reachable at {MONGODB_URL}, database '{DATABASE_NAME}'")
        return 0
    except Exception:
        return 1
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
