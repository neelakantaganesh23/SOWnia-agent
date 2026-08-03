"""CORS configuration helper.

Provides CORS middleware setup using application settings.
"""

from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings


def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware on the FastAPI application.

    Only allows origins specified in the ALLOWED_ORIGINS setting.

    Args:
        app: FastAPI application instance.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
