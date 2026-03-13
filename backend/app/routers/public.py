"""
Public API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from typing import List

from app.config import get_supported_language_pairs
from app.models.schemas import LanguagePair, LoginRequest, Token
from app.utils.auth import authenticate_user, create_access_token
from app.config import settings

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/languages", response_model=List[LanguagePair])
async def get_languages():
    """Get list of supported language pairs."""
    return get_supported_language_pairs()


@router.post("/auth/login", response_model=Token)
async def login(credentials: LoginRequest):
    """Admin login endpoint."""
    if not authenticate_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": credentials.username},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token)


@router.get("/health")
async def health_check():
    """Public health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
