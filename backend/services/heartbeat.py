"""Liveness heartbeat for running jobs, backed by Redis.

A running job writes a short-lived Redis key (``hb:{run_id}``) on a fixed
wall-clock interval. Admission control treats a job as alive only while that key
exists. Because the key carries a TTL, a job whose worker dies (e.g. SIGKILL)
stops refreshing it and the key auto-expires — so the job stops counting toward
the concurrency caps without anyone marking it failed. This is multi-worker safe
(liveness is per-job, not per-worker-restart) and needs no DB schema change.
"""

import os
import threading
from contextlib import contextmanager

import redis

from config.limits import HEARTBEAT_INTERVAL_SECONDS, JOB_HEARTBEAT_TTL_SECONDS

_REDIS_URL = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
_redis = redis.Redis.from_url(_REDIS_URL)

_KEY_PREFIX = "hb:"


def _key(run_id: int) -> str:
    return f"{_KEY_PREFIX}{run_id}"


def beat(run_id: int) -> None:
    """Write/refresh a run's liveness key with a fresh TTL."""
    _redis.set(_key(run_id), "1", ex=JOB_HEARTBEAT_TTL_SECONDS)


def clear(run_id: int) -> None:
    """Remove a run's liveness key (called when a job finishes normally)."""
    _redis.delete(_key(run_id))


def alive_run_ids(run_ids: list[int]) -> set[int]:
    """Return the subset of run_ids whose heartbeat key still exists.

    Uses a single pipelined round trip regardless of how many ids are checked.
    """
    if not run_ids:
        return set()
    pipe = _redis.pipeline()
    for rid in run_ids:
        pipe.exists(_key(rid))
    results = pipe.execute()
    return {rid for rid, exists in zip(run_ids, results) if exists}


def count_alive(run_ids: list[int]) -> int:
    """Count how many of the given runs are currently alive."""
    return len(alive_run_ids(run_ids))


@contextmanager
def heartbeat(run_id: int):
    """Emit a liveness heartbeat for the duration of the wrapped work.

    Writes an immediate beat on entry (so the run is 'alive' before its status
    flips to progress), then a background daemon thread refreshes it every
    ``HEARTBEAT_INTERVAL_SECONDS``. Because the beat runs on a wall-clock timer
    rather than per training step, a slow-but-alive job (long epoch) keeps
    beating and is never mistaken for dead. On exit — normal or exception — the
    thread stops and the key is deleted so the slot frees immediately; if the
    process is killed outright, the key simply expires after the TTL.
    """
    stop = threading.Event()

    def _loop():
        while not stop.is_set():
            try:
                beat(run_id)
            except Exception:
                pass  # a transient Redis hiccup shouldn't crash the job
            stop.wait(HEARTBEAT_INTERVAL_SECONDS)

    beat(run_id)
    thread = threading.Thread(target=_loop, name=f"heartbeat-{run_id}", daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=5)
        try:
            clear(run_id)
        except Exception:
            pass
