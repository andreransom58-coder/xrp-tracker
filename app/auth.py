from fastapi import Depends, HTTPException, Header, status

from .config import get_settings


def verify_api_key(x_api_key: str = Header(default="")):
    settings = get_settings()
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
    return
