from __future__ import annotations

import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.settings import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    email: str


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    """
    Minimal demo login (no new libraries):
    - Any email is accepted
    - Password must match settings.demo_password
    - Returns a random token (not stored yet)
    """
    demo_pw = getattr(settings, "demo_password", None)
    if not demo_pw:
        raise HTTPException(status_code=500, detail="demo_password not configured")

    if payload.password != demo_pw:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_urlsafe(32)
    return LoginResponse(token=token, email=payload.email.strip().lower())