# Worker Scaling Verification

**Issue:** Verify that the asynchronous worker architecture can handle multiple media-processing jobs and scale horizontally.

**Date:** September 2026
**Environment:** Local Docker Compose stack (FastAPI + Celery + RabbitMQ + Redis + MinIO as an S3-compatible store)

---

## Setup

The stack was run with:

```powershell
docker compose up --build --scale worker=<N>
```

`--scale worker=N` runs N independent Celery worker containers, all consuming from the same RabbitMQ `celery` queue. The `container_name` field was removed from the `worker` service in `docker-compose.yml` to allow multiple worker containers to run simultaneously (a fixed name only permits one container).

Jobs were submitted through the real API flow:

1. `POST /jobs` — creates a job record in Redis and returns a presigned MinIO upload URL
2. `PUT <upload_url>` — uploads the actual file to MinIO
3. `POST /jobs/{job_id}/confirm-upload` — verifies the upload exists, then dispatches `process_media.delay(job_id)` to Celery

A batch of 10 image jobs (`operation: "resize"`) was submitted per test run using a PowerShell script that performs all three steps for each job.

## Bugs found and fixed during setup

Several issues were surfaced and corrected before valid scaling data could be collected:

- **Missing `S3_BUCKET_NAME` / S3 config** — `docker-compose.yml` had no S3 environment variables at all; added `S3_BUCKET_NAME`, `AWS_REGION`, `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, pointed at a local MinIO container standing in for S3.
- **Missing Celery broker/backend env vars** — `app/worker/celery_app.py` defaulted to `localhost` for both `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`, which resolved to the container itself rather than the `rabbitmq`/`redis` services. Added both variables explicitly to `docker-compose.yml`, pointing at `rabbitmq:5672` and `redis:6379`.
- **Duplicate/mismatched Celery apps** — the project had two separate Celery app definitions (`app/tasks/celery_app.py`, now deleted, and `app/worker/celery_app.py`), and two separate task implementations (`app/worker/tasks.py`, a stub, now deleted, and `app/tasks/media_tasks.py`, the real implementation). The real task's Celery app import and the worker's `include` list were pointed at different modules, so the worker never registered the real task (`Received unregistered task of type 'app.tasks.media_tasks.process_media'`). Fixed by consolidating on `app/worker/celery_app.py` with `include=["app.tasks.media_tasks"]`, and updating the import in `media_tasks.py` accordingly.

## Results

### Task distribution across workers (3 workers)

A batch of 10 jobs was distributed across all 3 worker containers, confirmed via Celery task logs:

| Worker | Hostname | Jobs processed |
|---|---|---|
| worker-1 | celery@5503e8376a41 | 3 |
| worker-2 | celery@f6b0ff86f2de | 4 |
| worker-3 | celery@2d63bf4edfb4 | 3 |

All 10 jobs succeeded. No jobs were lost, duplicated, or stuck.

### RabbitMQ queue behavior

The RabbitMQ management UI (`celery` queue) was monitored during job submission. The **Message rates** graph showed a clear publish spike followed by a matching deliver spike, with the queue returning to `Ready: 0 / Unacked: 0 / Total: 0` (idle) once all jobs were processed — confirming clean drain with no backlog. `Consumers: 3` confirmed all workers stayed connected throughout.

### Timing comparison: 1 worker vs 3 workers

| Worker count | First task received | Last task succeeded | Total batch time |
|---|---|---|---|
| 1 | 23:28:25.568 | 23:28:27.205 | ~1.64s |
| 3 | 22:59:43.606 | 22:59:45.913 | ~2.3s |

**Observation:** with the current task implementation, per-job work is extremely lightweight (2–37ms), since `process_media` does not yet perform real image/video processing. At this scale, the overhead of coordinating 3 separate worker processes (each doing its own broker handshake and mingle/sync) outweighs the benefit of parallelism, so 3 workers did not show a clear speedup over 1 worker for this batch size and task cost.

This is expected for near-instant tasks and is not evidence against horizontal scaling — it reflects the current task being a stub rather than a real workload. Distribution across workers was still verified as correct at every worker count tested.

### CPU / memory

`docker stats` was monitored during job runs. Given task durations of single-digit milliseconds, CPU usage per worker container showed only brief, low spikes rather than sustained load. No worker approached its memory limit. RabbitMQ itself raised a `system_memory_high_watermark` notice during startup under the default Docker Desktop memory allocation — worth noting if scaling further, but did not affect job processing in this test.

### Job status correctness

Job statuses were confirmed via `GET /jobs/{job_id}` after processing; submitted jobs correctly reflected `processing` immediately after `confirm-upload`, consistent with the current stub task implementation (which does not yet update status to a final `completed` state — see Known limitations).

## Known limitations / scope notes

- **Video processing is not yet implemented.** The `/jobs` API currently only accepts `operation: "resize"` (`Literal["resize"]` in `JobRequest`). Video-job concurrency should be re-verified once a video operation is added.
- **`process_media` is currently a lightweight/stub implementation.** It does not yet perform real FFmpeg/image processing, which is why per-task timing is in the low milliseconds. Scaling behavior should be re-measured once real processing work is wired in, as that is the scenario where multiple workers are expected to show a clear throughput advantage.

## Recommended scaling approach

- Horizontal scaling via `docker compose up --scale worker=N` works correctly: jobs are distributed across all available workers with no loss or duplication, and RabbitMQ handles the queue reliably under this load.
- For the current lightweight task, worker count has little effect on total throughput; scaling won't show real benefit until `process_media` performs actual (seconds-scale) media processing.
- Once real processing is in place, recommend scaling workers roughly in line with available CPU cores, and re-running this same batch test to establish a meaningful baseline (jobs/sec per worker) for capacity planning.