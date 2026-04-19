"""Emergency realtime SSE stream endpoints."""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import DESCENDING

from app.api.v1.dependencies import get_user_service
from app.domain.models.user import User, UserRole
from app.domain.services.user_service import UserService
from app.infrastructure.database.mongodb import get_database
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str
from app.infrastructure.security.jwt import decode_token

router = APIRouter()

POLL_INTERVAL_SECONDS = 3.0
HEARTBEAT_INTERVAL_SECONDS = 10.0
LOOP_SLEEP_SECONDS = 0.5
MAX_CHANGED_ITEMS = 200

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

_indexes_ready = False
_indexes_lock = asyncio.Lock()
_optional_bearer = HTTPBearer(auto_error=False)


async def get_stream_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_bearer),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Authenticate SSE stream users via bearer header or access_token query string."""
    token = credentials.credentials if credentials and credentials.credentials else None
    if not token:
        token = request.query_params.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await user_service.get_user_by_id(str(user_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def _ensure_operator(user: User):
    """Allow only admin and technician roles for emergency stream access."""
    if user.role not in {UserRole.ADMIN, UserRole.TECHNICIAN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for emergency operations",
        )


async def _ensure_indexes(db: AsyncIOMotorDatabase):
    """Ensure updated_at indexes used by stream diff polling."""
    global _indexes_ready
    if _indexes_ready:
        return

    async with _indexes_lock:
        if _indexes_ready:
            return

        await db["emergency_events"].create_index(
            [("updated_at", DESCENDING)],
            name="idx_emergency_updated_at",
        )
        await db["hazard_layers"].create_index(
            [("updated_at", DESCENDING)],
            name="idx_hazard_updated_at",
        )
        _indexes_ready = True


def _sse_event(event: str, payload: Dict[str, Any]) -> str:
    encoded = json.dumps(jsonable_encoder(payload), separators=(",", ":"))
    return f"event: {event}\ndata: {encoded}\n\n"


async def _load_latest_updated_at(
    collection: AsyncIOMotorCollection,
) -> Optional[datetime]:
    doc = await collection.find_one(
        filter={},
        projection={"updated_at": 1},
        sort=[("updated_at", DESCENDING)],
    )
    if not doc:
        return None

    updated_at = doc.get("updated_at")
    return updated_at if isinstance(updated_at, datetime) else None


async def _load_changed_documents(
    collection: AsyncIOMotorCollection,
    last_seen_updated_at: datetime,
    projection: Optional[Dict[str, int]] = None,
) -> List[Dict[str, Any]]:
    cursor = (
        collection.find({"updated_at": {"$gt": last_seen_updated_at}}, projection)
        .sort("updated_at", 1)
        .limit(MAX_CHANGED_ITEMS)
    )

    documents: List[Dict[str, Any]] = []
    async for doc in cursor:
        converted = convert_objectid_to_str(doc)
        if "id" not in converted and "_id" in converted:
            converted["id"] = str(converted["_id"])
        documents.append(converted)
    return documents


def _extract_max_updated_at(documents: List[Dict[str, Any]], fallback: datetime) -> datetime:
    max_updated_at = fallback
    for doc in documents:
        updated_at = doc.get("updated_at")
        if isinstance(updated_at, datetime) and updated_at > max_updated_at:
            max_updated_at = updated_at
    return max_updated_at


async def _stream_collection_updates(
    request: Request,
    collection: AsyncIOMotorCollection,
    stream_name: str,
    projection: Optional[Dict[str, int]] = None,
) -> AsyncGenerator[str, None]:
    last_seen_updated_at = await _load_latest_updated_at(collection) or datetime.min
    last_poll_at = time.monotonic()
    last_heartbeat_at = last_poll_at

    yield _sse_event(
        "connected",
        {
            "stream": stream_name,
            "poll_interval_seconds": int(POLL_INTERVAL_SECONDS),
            "heartbeat_interval_seconds": int(HEARTBEAT_INTERVAL_SECONDS),
            "last_seen_updated_at": (
                None if last_seen_updated_at == datetime.min else last_seen_updated_at.isoformat()
            ),
        },
    )

    while True:
        if await request.is_disconnected():
            break

        now = time.monotonic()

        if now - last_poll_at >= POLL_INTERVAL_SECONDS:
            documents = await _load_changed_documents(
                collection=collection,
                last_seen_updated_at=last_seen_updated_at,
                projection=projection,
            )
            if documents:
                last_seen_updated_at = _extract_max_updated_at(
                    documents=documents,
                    fallback=last_seen_updated_at,
                )
                yield _sse_event(
                    stream_name,
                    {
                        "stream": stream_name,
                        "count": len(documents),
                        "max_updated_at": last_seen_updated_at.isoformat(),
                        "items": documents,
                    },
                )
            last_poll_at = now

        if now - last_heartbeat_at >= HEARTBEAT_INTERVAL_SECONDS:
            yield _sse_event(
                "heartbeat",
                {
                    "stream": stream_name,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            last_heartbeat_at = now

        await asyncio.sleep(LOOP_SLEEP_SECONDS)


@router.get("/hazards")
async def stream_hazards(
    request: Request,
    current_user: User = Depends(get_stream_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Stream hazard layer updates for emergency board clients."""
    _ensure_operator(current_user)
    await _ensure_indexes(db)

    return StreamingResponse(
        _stream_collection_updates(
            request=request,
            collection=db["hazard_layers"],
            stream_name="hazards",
            projection={"vector_embedding": 0},
        ),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/events")
async def stream_events(
    request: Request,
    current_user: User = Depends(get_stream_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Stream emergency event updates for emergency board clients."""
    _ensure_operator(current_user)
    await _ensure_indexes(db)

    return StreamingResponse(
        _stream_collection_updates(
            request=request,
            collection=db["emergency_events"],
            stream_name="events",
        ),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )