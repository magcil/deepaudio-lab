"""Admission control for background jobs.

Before a training/evaluation job is dispatched, this enforces both a per-type
cap and an overall cap, for the requesting user and for the whole system. An
"active" job is one that is queued (pending) or running with a live heartbeat;
a run whose worker died stops counting once its Redis heartbeat key expires, so
caps self-heal without ever marking a live job failed.
"""

from collections.abc import Callable

from sqlalchemy.orm import Session

from config.limits import (
    MAX_SYSTEM_EVALUATIONS,
    MAX_SYSTEM_JOBS,
    MAX_SYSTEM_TRAININGS,
    MAX_USER_EVALUATIONS,
    MAX_USER_JOBS,
    MAX_USER_TRAININGS,
)
from exceptions.exceptions import SystemJobLimitError, UserJobLimitError
from repositories import run_repository
from services import heartbeat


def _active_count(pending_and_progress: tuple[int, list[int]]) -> int:
    """Combine queued (always counted) with running-and-alive (heartbeat-checked)."""
    pending_count, progress_ids = pending_and_progress
    return pending_count + heartbeat.count_alive(progress_ids)


def _enforce(
    db: Session,
    user_id: str,
    job_type: str,
    per_type: Callable[..., tuple[int, list[int]]],
    user_type_limit: int,
    system_type_limit: int,
) -> None:
    # Per-type caps (user first, then system).
    user_type = _active_count(per_type(db, user_id))
    if user_type >= user_type_limit:
        raise UserJobLimitError(job_type, user_type, user_type_limit)

    system_type = _active_count(per_type(db))
    if system_type >= system_type_limit:
        raise SystemJobLimitError(job_type, system_type, system_type_limit)

    # Overall caps across all job types.
    user_overall = _active_count(run_repository.active_jobs(db, user_id))
    if user_overall >= MAX_USER_JOBS:
        raise UserJobLimitError("job", user_overall, MAX_USER_JOBS)

    system_overall = _active_count(run_repository.active_jobs(db))
    if system_overall >= MAX_SYSTEM_JOBS:
        raise SystemJobLimitError("job", system_overall, MAX_SYSTEM_JOBS)


def check_can_start_training(db: Session, user_id: str) -> None:
    """Raise UserJobLimitError (429) or SystemJobLimitError (503) if a new
    training job would exceed the per-type or overall caps."""
    _enforce(
        db,
        user_id,
        "training",
        run_repository.active_trainings,
        MAX_USER_TRAININGS,
        MAX_SYSTEM_TRAININGS,
    )


def check_can_start_evaluation(db: Session, user_id: str) -> None:
    """Raise UserJobLimitError (429) or SystemJobLimitError (503) if a new
    evaluation job would exceed the per-type or overall caps."""
    _enforce(
        db,
        user_id,
        "evaluation",
        run_repository.active_evaluations,
        MAX_USER_EVALUATIONS,
        MAX_SYSTEM_EVALUATIONS,
    )
