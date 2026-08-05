"""FastAPI dependency that resolves the current authenticated user from the
httpOnly `access_token` cookie. Add `current_user: User = Depends(get_current_user)`
to any route that needs per-user scoping."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.auth.security import decode_access_token
from backend.db.session import get_db
from backend.models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user
