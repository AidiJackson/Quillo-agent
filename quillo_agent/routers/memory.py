"""
Memory and profile management endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from loguru import logger
from ..db import get_db
from ..schemas import ProfileIn, ProfileOut
from ..services import memory as memory_service
from ..auth import verify_api_key

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/profile", response_model=ProfileOut)
async def get_profile(
    user_id: str = Query(..., description="User identifier"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> ProfileOut:
    """
    Get user profile (auto-initializes if missing).

    Args:
        user_id: User identifier
        db: Database session

    Returns:
        ProfileOut with markdown content and timestamp
    """
    logger.info(f"GET /memory/profile: user_id={user_id}")
    profile_md = memory_service.get_or_init_profile(db, user_id)

    # Get updated_at timestamp
    from ..models import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    updated_at = profile.updated_at.isoformat() if profile else ""

    return ProfileOut(profile_md=profile_md, updated_at=updated_at)


@router.post("/profile", response_model=ProfileOut)
async def update_profile(
    request: ProfileIn,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> ProfileOut:
    """
    Update user profile markdown.

    Args:
        request: ProfileIn with user_id and profile_md
        db: Database session

    Returns:
        ProfileOut with updated content and timestamp
    """
    logger.info(f"POST /memory/profile: user_id={request.user_id}")
    updated_at = memory_service.update_profile(
        db,
        request.user_id,
        request.profile_md
    )
    return ProfileOut(
        profile_md=request.profile_md,
        updated_at=updated_at.isoformat()
    )
