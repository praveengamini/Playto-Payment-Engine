from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Single declarative base shared by all models."""
    pass