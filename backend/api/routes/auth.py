"""Auth routes — POST /api/v1/auth/{signup,login,logout}, GET /me,
GET /google/login, GET /google/callback.

JWT is issued as an httpOnly cookie so frontend/middleware.ts can gate
routes without needing to store/attach a bearer token in JS.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.auth.google_oauth import exchange_code_for_userinfo, get_google_authorize_url
from backend.auth.security import create_access_token, hash_password, verify_password
from backend.config import settings
from backend.db.session import get_db
from backend.models.user import User
from backend.schemas.auth import LoginRequest, SignupRequest, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()

COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = settings.JWT_EXPIRE_MINUTES * 60


def _set_auth_cookie(response: Response, user_id: str) -> None:
    token = create_access_token(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=not settings.is_development,
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


@router.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)) -> UserResponse:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    _set_auth_cookie(response, str(user.id))
    return UserResponse(id=str(user.id), email=user.email, full_name=user.full_name)


@router.post("/auth/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> UserResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    _set_auth_cookie(response, str(user.id))
    return UserResponse(id=str(user.id), email=user.email, full_name=user.full_name)


@router.post("/auth/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"message": "Logged out"}


@router.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=str(current_user.id), email=current_user.email, full_name=current_user.full_name)


@router.get("/auth/google/login", include_in_schema=False)
def google_login() -> RedirectResponse:
    return RedirectResponse(url=get_google_authorize_url())


@router.get("/auth/google/callback", include_in_schema=False)
async def google_callback(code: str, db: Session = Depends(get_db)) -> RedirectResponse:
    userinfo = await exchange_code_for_userinfo(code)
    if not userinfo or not userinfo.get("email"):
        return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/login?error=oauth_failed")

    user = db.query(User).filter(User.google_sub == userinfo["sub"]).first()
    if not user:
        # Link by email if an existing password account matches, else create new.
        user = db.query(User).filter(User.email == userinfo["email"]).first()
        if user:
            user.google_sub = userinfo["sub"]
        else:
            user = User(email=userinfo["email"], google_sub=userinfo["sub"], full_name=userinfo.get("name"))
            db.add(user)
        db.commit()
        db.refresh(user)

    redirect = RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/dashboard")
    _set_auth_cookie(redirect, str(user.id))
    return redirect
