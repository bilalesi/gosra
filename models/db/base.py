from sqlalchemy.orm import DeclarativeBase
from sqlalchemy_continuum import make_versioned

make_versioned(user_cls="User")


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass
