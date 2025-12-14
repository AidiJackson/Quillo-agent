"""
Authentication and authorization utilities
"""
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings

security = HTTPBearer()


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Verify API key from Authorization header.

    Args:
        credentials: HTTPAuthorizationCredentials from Security

    Returns:
        The valid API key

    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    if not settings.quillo_api_key:
        raise HTTPException(
            status_code=500,
            detail="API key not configured on server"
        )

    if credentials.credentials != settings.quillo_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return credentials.credentials
