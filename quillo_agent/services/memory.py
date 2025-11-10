"""
Memory and profile management service
"""
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger
from ..models import User, UserProfile, FeedbackEvent


DEFAULT_PROFILE_TEMPLATE = """# User Profile: {user_id}

## Core Identity
(user editable)

## Personal Interests
(user editable)

## Tone & Style
**Prefers:**

**Avoid:**

## Negotiation Patterns (Analytics)
(auto notes)

## Recent Wins
(user editable)

## Active Goals
(user editable)

## Highlights (Auto)
(appended by feedback)
"""


def get_or_init_profile(db: Session, user_id: str) -> str:
    """
    Get existing profile or initialize with default template.

    Args:
        db: Database session
        user_id: User identifier

    Returns:
        Profile markdown content
    """
    # Ensure user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id)
        db.add(user)
        db.commit()
        logger.info(f"Created new user: {user_id}")

    # Get or create profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile_md = DEFAULT_PROFILE_TEMPLATE.format(user_id=user_id)
        profile = UserProfile(user_id=user_id, profile_md=profile_md)
        db.add(profile)
        db.commit()
        logger.info(f"Initialized profile for user: {user_id}")
        return profile_md

    return profile.profile_md


def update_profile(db: Session, user_id: str, profile_md: str) -> datetime:
    """
    Update user profile markdown.

    Args:
        db: Database session
        user_id: User identifier
        profile_md: New profile content

    Returns:
        Updated timestamp
    """
    # Ensure user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id)
        db.add(user)
        db.commit()

    # Update or create profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile:
        profile.profile_md = profile_md
        profile.updated_at = datetime.utcnow()
    else:
        profile = UserProfile(user_id=user_id, profile_md=profile_md)
        db.add(profile)

    db.commit()
    db.refresh(profile)
    logger.info(f"Updated profile for user: {user_id}")
    return profile.updated_at


def record_feedback(
    db: Session,
    user_id: str,
    tool: str,
    outcome: bool,
    signals: dict = None
) -> None:
    """
    Record feedback event and append to profile Highlights section.

    Args:
        db: Database session
        user_id: User identifier
        tool: Tool that was used
        outcome: True for success, False for failure
        signals: Additional signals/metadata
    """
    # Ensure user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id)
        db.add(user)
        db.commit()

    # Record feedback event
    event = FeedbackEvent(
        user_id=user_id,
        tool=tool,
        outcome=outcome,
        signals=signals
    )
    db.add(event)
    db.commit()
    logger.info(f"Recorded feedback for user {user_id}: {tool} -> {outcome}")

    # Append to profile Highlights
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile_md = get_or_init_profile(db, user_id)
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    # Format highlight entry
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    emoji = "✅" if outcome else "❌"
    highlight = f"\n- {emoji} {tool} at {timestamp}"
    if signals:
        highlight += f" | signals: {signals}"

    # Append to Highlights section
    if "## Highlights (Auto)" in profile.profile_md:
        profile.profile_md = profile.profile_md.replace(
            "## Highlights (Auto)\n(appended by feedback)",
            f"## Highlights (Auto)\n(appended by feedback){highlight}"
        )
    else:
        profile.profile_md += f"\n{highlight}"

    profile.updated_at = datetime.utcnow()
    db.commit()
    logger.debug(f"Appended highlight to profile for user: {user_id}")
