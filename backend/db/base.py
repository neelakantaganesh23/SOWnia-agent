"""SQLAlchemy declarative base.

Imports every model module so Alembic's autogenerate can discover all
tables from this single import.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import models so they register on Base.metadata (used by Alembic env.py).
from backend.models import user, uploaded_file, review  # noqa: E402,F401
