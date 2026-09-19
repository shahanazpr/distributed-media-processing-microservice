import pytest
from PIL import Image

from app.media.image_processor import (
    add_watermark,
    compress_image,
    crop_image,
    resize_image,
    validate_image,
)


def test_validate_image(tmp_path):
    image_path = tmp_path / "input.jpg"

    image = Image.new("RGB", (100, 100), "red")
    image.save(image_path)

    result = validate_image(str(image_path))

    assert result.size == (100, 100)
    assert result.format == "JPEG"


def test_validate_invalid_image(tmp_path):
    image_path = tmp_path / "invalid.jpg"
    image_path.write_text("This is not a valid image")

    with pytest.raises(ValueError, match="Invalid or corrupted image"):
        validate_image(str(image_path))


def test_validate_unsupported_format(tmp_path):
    image_path = tmp_path / "input.bmp"

    image = Image.new("RGB", (100, 100), "red")
    image.save(image_path)

    with pytest.raises(ValueError, match="Unsupported image format"):
        validate_image(str(image_path))


def test_crop_image():
    image = Image.new("RGB", (100, 100), "red")

    result = crop_image(image, 10, 10, 60, 60)

    assert result.size == (50, 50)


def test_resize_image():
    image = Image.new("RGB", (100, 100), "red")

    result = resize_image(image, 200, 150)

    assert result.size == (200, 150)


def test_compress_image(tmp_path):
    image = Image.new("RGB", (100, 100), "red")
    output_path = tmp_path / "compressed.jpg"

    compress_image(image, str(output_path), quality=80)

    assert output_path.exists()

    with Image.open(output_path) as result:
        assert result.size == (100, 100)


def test_compress_invalid_quality(tmp_path):
    image = Image.new("RGB", (100, 100), "red")
    output_path = tmp_path / "compressed.jpg"

    with pytest.raises(ValueError, match="Quality must be between 1 and 100"):
        compress_image(image, str(output_path), quality=101)


def test_add_watermark(tmp_path):
    image = Image.new("RGB", (300, 200), "blue")
    output_path = tmp_path / "watermarked.png"

    add_watermark(
        image,
        "Test Watermark",
        str(output_path),
    )

    assert output_path.exists()

    with Image.open(output_path) as result:
        assert result.size == (300, 200)


def test_add_empty_watermark(tmp_path):
    image = Image.new("RGB", (300, 200), "blue")
    output_path = tmp_path / "watermarked.png"

    with pytest.raises(ValueError, match="Watermark text cannot be empty"):
        add_watermark(
            image,
            "",
            str(output_path),
        )


def test_add_watermark_top_left(tmp_path):
    image = Image.new("RGB", (300, 200), "blue")
    output_path = tmp_path / "watermarked.png"

    add_watermark(
        image,
        "Test Watermark",
        str(output_path),
        position="top-left",
        opacity=0.5,
    )

    assert output_path.exists()

    with Image.open(output_path) as result:
        assert result.size == (300, 200)


def test_add_watermark_center(tmp_path):
    image = Image.new("RGB", (300, 200), "blue")
    output_path = tmp_path / "watermarked.png"

    add_watermark(
        image,
        "Test Watermark",
        str(output_path),
        position="center",
        opacity=0.8,
    )

    assert output_path.exists()

    with Image.open(output_path) as result:
        assert result.size == (300, 200)


def test_add_watermark_invalid_position(tmp_path):
    image = Image.new("RGB", (300, 200), "blue")
    output_path = tmp_path / "watermarked.png"

    with pytest.raises(ValueError, match="Invalid watermark position"):
        add_watermark(
            image,
            "Test Watermark",
            str(output_path),
            position="invalid",
        )


def test_add_watermark_invalid_opacity(tmp_path):
    image = Image.new("RGB", (300, 200), "blue")
    output_path = tmp_path / "watermarked.png"

    with pytest.raises(
        ValueError,
        match="Watermark opacity must be between 0 and 1",
    ):
        add_watermark(
            image,
            "Test Watermark",
            str(output_path),
            opacity=1.5,
        )


def test_add_image_watermark(tmp_path):
    image = Image.new("RGB", (300, 200), "blue")

    watermark_path = tmp_path / "watermark.png"

    watermark = Image.new(
        "RGBA",
        (100, 50),
        (255, 255, 255, 255),
    )
    watermark.save(watermark_path)

    output_path = tmp_path / "watermarked.png"

    add_watermark(
        image,
        "",
        str(output_path),
        position="bottom-right",
        opacity=0.5,
        watermark_path=str(watermark_path),
    )

    assert output_path.exists()

    with Image.open(output_path) as result:
        assert result.size == (300, 200)


def test_add_image_watermark_missing_asset(tmp_path):
    image = Image.new("RGB", (300, 200), "blue")

    output_path = tmp_path / "watermarked.png"

    missing_watermark = tmp_path / "missing.png"

    with pytest.raises(
        FileNotFoundError,
        match="Watermark asset not found",
    ):
        add_watermark(
            image,
            "",
            str(output_path),
            watermark_path=str(missing_watermark),
        )


def test_add_image_watermark_invalid_asset(tmp_path):
    image = Image.new("RGB", (300, 200), "blue")

    watermark_path = tmp_path / "invalid.png"
    watermark_path.write_text("not a real image")

    output_path = tmp_path / "watermarked.png"

    with pytest.raises(
        ValueError,
        match="Invalid watermark asset",
    ):
        add_watermark(
            image,
            "",
            str(output_path),
            watermark_path=str(watermark_path),
        )