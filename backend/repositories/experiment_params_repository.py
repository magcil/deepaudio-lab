from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import RepositoryError
from models.experiment_params import ExperimentParams


def update_experiment_params(db: Session, exp_params: ExperimentParams) -> ExperimentParams:
    """Persist updates to an existing experiment parameters record.

    Assumes the provided ``exp_params`` instance is already attached to
    the current SQLAlchemy session and has been modified prior to calling
    this function. The session is committed, and the instance is refreshed
    to reflect the latest database state.

    Args:
        db (Session): Active SQLAlchemy session.
        exp_params (ExperimentParams): The existing experiment parameters
            instance with pending changes.

    Raises:
        RepositoryError: If a database error occurs during commit.

    Returns:
        ExperimentParams: The updated and refreshed experiment parameters instance.
    """
    try:
        db.commit()
        db.refresh(exp_params)
        return exp_params

    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to update experiment params") from e
