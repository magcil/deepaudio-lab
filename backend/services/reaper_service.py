"""Maintenance reaper: reconcile dead jobs and reclaim old datasets.

Run periodically by the maintenance worker (Celery Beat). Two independent
sweeps:

1. reap_stale_runs — runs that display as 'In Progress' but whose worker died
   (heartbeat expired) are marked 'Failure', so the UI reflects reality. The
   concurrency caps already ignore them via the heartbeat; this is the cosmetic
   counterpart that also makes the status durable.

2. reap_old_datasets — when enabled, datasets older than the retention window
   that are NOT referenced by any active (queued/running) job are deleted from
   S3 and the database. Off by default because it removes real user data.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from config.limits import (
    DATASET_RETENTION_ENABLED,
    DATASET_RETENTION_SECONDS,
)
from repositories import dataset_repository, run_repository
from services import dataset_service, heartbeat

logger = logging.getLogger(__name__)


def reap_stale_runs(db: Session) -> int:
    """Mark in-progress runs with no live heartbeat as failed.

    Returns the number of runs reconciled.
    """
    progress_ids = run_repository.progress_run_ids(db)
    if not progress_ids:
        return 0

    alive = heartbeat.alive_run_ids(progress_ids)
    dead = [run_id for run_id in progress_ids if run_id not in alive]

    reaped = 0
    for run_id in dead:
        if run_repository.fail_if_progress(db, run_id):
            reaped += 1

    if reaped:
        logger.info("Reaper: marked %d stale run(s) as failed: %s", reaped, dead)
    return reaped


def reap_old_datasets(db: Session) -> int:
    """Delete datasets older than the retention window that no active job uses.

    No-op unless DATASET_RETENTION_ENABLED is set. Returns the number deleted.
    """
    if not DATASET_RETENTION_ENABLED:
        return 0

    cutoff = datetime.now(UTC) - timedelta(seconds=DATASET_RETENTION_SECONDS)
    in_use = run_repository.active_dataset_ids(db)
    candidates = dataset_repository.get_created_before(db, cutoff)

    deleted = 0
    for dataset in candidates:
        if dataset.id in in_use:
            continue
        # Audit trail: this removes real user data.
        logger.info(
            "Reaper: deleting dataset id=%s name=%r user=%s created_at=%s (retention exceeded, not in use)",
            dataset.id,
            dataset.name,
            dataset.user_id,
            dataset.created_at,
        )
        dataset_service.delete(db, dataset.id)
        deleted += 1

    if deleted:
        logger.info("Reaper: deleted %d old dataset(s)", deleted)
    return deleted


def run_reaper(db: Session) -> dict:
    """Run both sweeps in order (stale runs first so dataset 'in use' is accurate)."""
    runs_failed = reap_stale_runs(db)
    datasets_deleted = reap_old_datasets(db)
    return {"runs_failed": runs_failed, "datasets_deleted": datasets_deleted}
