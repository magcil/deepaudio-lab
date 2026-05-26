# models/user.py

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.session import Base


class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True)  # Keycloak sub
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    runs = relationship("Run", back_populates="creator", cascade="all, delete-orphan", passive_deletes=True)
