from contextlib import contextmanager
import time

from prometheus_client import Counter, Histogram

# --- Job counters ---
JOBS_TOTAL = Counter(
    "media_jobs_total",
    "Total number of media-processing jobs received",
)

JOBS_SUCCEEDED = Counter(
    "media_jobs_succeeded_total",
    "Total number of successfully completed jobs",
)

JOBS_FAILED = Counter(
    "media_jobs_failed_total",
    "Total number of failed jobs",
)

JOB_STATUS_COUNT = Counter(
    "media_job_status_total",
    "Count of jobs by status transition",
    ["status"],
)

# --- Processing duration ---
JOB_PROCESSING_DURATION = Histogram(
    "media_job_processing_duration_seconds",
    "Time spent processing a media job, in seconds",
)

# --- Worker / queue activity ---
WORKER_ACTIVE_JOBS = Counter(
    "media_worker_jobs_picked_up_total",
    "Total number of jobs picked up by a worker",
)

QUEUE_PUBLISHED_TOTAL = Counter(
    "media_queue_published_total",
    "Total number of job messages published to the queue",
)


@contextmanager
def track_job_duration():
    """Context manager to time a block of code and record it in the duration histogram."""
    start = time.perf_counter()
    try:
        yield
    finally:
        JOB_PROCESSING_DURATION.observe(time.perf_counter() - start)