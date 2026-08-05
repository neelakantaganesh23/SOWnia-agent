"""Pydantic models for the auth endpoints."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr = Field(..., description="Account email")
    password: str = Field(..., min_length=8, description="Account password (min 8 chars)")
    full_name: Optional[str] = Field(None, description="Display name")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Account email")
    password: str = Field(..., description="Account password")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: Optional[str] = None
