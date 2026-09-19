import pytest
from unittest.mock import MagicMock, patch

from app.services import cdn_service


@pytest.fixture
def mock_settings_with_domain():
    with patch("app.services.cdn_service.get_settings") as mock_get:
        mock_get.return_value.cloudfront_domain = "d123abc4567.cloudfront.net"
        yield mock_get


@pytest.fixture
def mock_settings_no_domain():
    with patch("app.services.cdn_service.get_settings") as mock_get:
        mock_get.return_value.cloudfront_domain = ""
        yield mock_get


def test_build_cdn_url(mock_settings_with_domain):
    url = cdn_service.build_cdn_url("output/job-1/processed/image.jpg")
    assert url == "https://d123abc4567.cloudfront.net/output/job-1/processed/image.jpg"


def test_build_cdn_url_raises_when_not_configured(mock_settings_no_domain):
    with pytest.raises(cdn_service.CDNConfigError):
        cdn_service.build_cdn_url("output/job-1/processed/image.jpg")


def test_get_output_cdn_info_object_missing(mock_settings_with_domain):
    mock_storage = MagicMock()
    mock_storage.object_exists.return_value = False

    result = cdn_service.get_output_cdn_info("output/job-1/processed/missing.jpg", storage=mock_storage)

    assert result["cdn_url"] is None
    assert "error" in result


def test_get_output_cdn_info_success(mock_settings_with_domain):
    mock_storage = MagicMock()
    mock_storage.object_exists.return_value = True

    result = cdn_service.get_output_cdn_info("output/job-1/processed/image.jpg", storage=mock_storage)

    assert result["s3_key"] == "output/job-1/processed/image.jpg"
    assert result["cdn_url"] == "https://d123abc4567.cloudfront.net/output/job-1/processed/image.jpg"


def test_get_output_cdn_info_video_thumbnail(mock_settings_with_domain):
    mock_storage = MagicMock()
    mock_storage.object_exists.return_value = True

    result = cdn_service.get_output_cdn_info("output/job-1/thumbnail/video.jpg", storage=mock_storage)

    assert result["cdn_url"].endswith("output/job-1/thumbnail/video.jpg")