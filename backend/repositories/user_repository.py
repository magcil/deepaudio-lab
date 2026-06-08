# repositories/user_repository.py

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import RepositoryError
from models.user import User


def delete_by_id(db: Session, id: str) -> None:
    """Delete a user by their Keycloak sub. Cascades to all owned runs.

    Args:
        db (Session): Active SQLAlchemy session.
        id (str): Keycloak subject (sub) of the user to delete.

    Raises:
        RepositoryError: If the database operation fails.
    """
    try:
        user = db.query(User).filter(User.id == id).first()
        if user is not None:
            db.delete(user)
            db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError(f"Failed to delete user '{id}'") from e


def upsert(
    db: Session, id: str, username: str, email: str | None, first_name: str | None, last_name: str | None
) -> None:
    """Insert user if not exists, update their fields if anything changed.

    Args:
        db (Session): Active SQLAlchemy session.
        id (str): Keycloak subject (sub) — stable unique identifier.
        username (str): Keycloak preferred_username.
        email (str | None): User email.
        first_name (str | None): Given name.
        last_name (str | None): Family name.

    Raises:
        RepositoryError: If the database operation fails.
    """
    try:
        user = db.query(User).filter(User.id == id).first()
        if user is None:
            db.add(User(id=id, username=username, email=email, first_name=first_name, last_name=last_name))
        else:
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError(f"Failed to upsert user '{id}'") from e
