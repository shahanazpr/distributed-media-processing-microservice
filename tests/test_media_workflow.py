from pathlib import Path
from unittest.mock import Mock

import io

import pytest
from botocore.exceptions import (
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)
from PIL import Image

from app.storage.media_workflow import S3MediaWorkflow
from app.tasks.media_tasks import process_media


def test_original_key():
    key = S3MediaWorkflow.original_key(
        "job123",
        "video.mp4",
    )

    assert key == "input/job123/original/video.mp4"


def test_processed_key():
    key = S3MediaWorkflow.processed_key(
        "job123",
        "video.mp4",
    )

    assert key == "output/job123/processed/video.mp4"


def test_thumbnail_key():
    key = S3MediaWorkflow.thumbnail_key(
        "job123",
        "thumbnail.jpg",
    )

    assert key == "output/job123/thumbnail/thumbnail.jpg"


def test_filename_path_is_sanitized():
    key = S3MediaWorkflow.original_key(
        "job123",
        "C:\\uploads\\video.mp4",
    )

    assert key == "input/job123/original/video.mp4"