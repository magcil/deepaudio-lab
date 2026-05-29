# models/user.py

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.session import Base


class User(Base):
    """Local mirror of a Keycloak user, kept in sync on every authenticated request.

    The primary key is the Keycloak subject (`sub`) claim, so the local record
    is always aligned with the identity provider. The record is upserted in
    `get_current_user` each time a valid token is presented, ensuring the local
    table reflects the latest profile information from the JWT.

    Attributes:
        id (str): Keycloak subject identifier (`sub`), used as the primary key.
        username (str): The user's Keycloak username. Unique across all users.
        email (str | None): The user's email address.
        first_name (str | None): The user's first name.
        last_name (str | None): The user's last name.
        created_at (datetime): Timestamp of when the local record was first created.
        runs (list[Run]): All runs created by this user. Deleted automatically
            when the user is removed (cascade delete-orphan).
    """

    __tablename__ = "user"

    id = Column(String, primary_key=True)  # Keycloak sub
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    runs = relationship("Run", back_populates="creator", cascade="all, delete-orphan", passive_deletes=True)
    datasets = relationship("Dataset", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)
