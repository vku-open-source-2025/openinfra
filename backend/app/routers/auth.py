from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.mongodb import get_database


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    expires_in_minutes: int


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db=Depends(get_database)):
    admins = db["admins"]
    user = await admins.find_one({"username": payload.username})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    access_token = create_access_token(
        data={"sub": payload.username, "role": user.get("role", "admin")},
        expires_delta=timedelta(minutes=settings.ADMIN_JWT_EXPIRE_MINUTES),
    )

    return TokenResponse(
        token=access_token,
        expires_in_minutes=settings.ADMIN_JWT_EXPIRE_MINUTES,
    )
