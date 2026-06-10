from pathlib import Path

import aiosqlite
from fastapi import APIRouter, Response, status

from core import settings

router = APIRouter(prefix="/health", tags=["System Health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_probe() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_probe(response: Response) -> dict[str, str]:
    try:
        db_path = Path(settings.DATABASE_URL)
        async with aiosqlite.connect(db_path) as db:
            async with db.execute("SELECT 1") as cursor:
                await cursor.fetchone()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unready", "reason": str(e)}
