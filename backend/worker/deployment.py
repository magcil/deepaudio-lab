import pickle
import sys
from pathlib import Path

import models  # noqa: F401 — registers all SQLAlchemy models in this process
from db.session import SessionLocal
from services.deployment_service import build_bundle
from worker.app import celery_app

sys.path.insert(0, str(Path(__file__).parent.parent))


@celery_app.task(bind=True)
def run_deployment(self, run_id: int, user_id: str, name: str):
    """Build a self-contained inference zip bundle for a trained run.

    Progress states pushed to Redis:
        PROGRESS {"step": "<description>", "progress": <0-100>}
        SUCCESS  {}

    Args:
        run_id (int): Primary key of the run to deploy.
        user_id (str): Keycloak sub of the run owner.
        name (str): User-provided bundle name.
    """
    def progress_callback(step: str, progress: int) -> None:
        self.update_state(state="PROGRESS", meta={"step": step, "progress": progress})

    db = SessionLocal()
    try:
        self.update_state(state="PROGRESS", meta={"step": "Fetching parameters", "progress": 5})
        build_bundle(
            db=db,
            run_id=run_id,
            user_id=user_id,
            name=name,
            progress_callback=progress_callback,
        )
    except Exception as exc:
        try:
            pickle.dumps(exc)
        except Exception:
            raise RuntimeError(f"{type(exc).__name__}: {exc}") from None
        raise
    finally:
        db.close()

    return {"status": "done"}
