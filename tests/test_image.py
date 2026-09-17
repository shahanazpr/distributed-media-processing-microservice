from PIL import Image
import pytest

from app.processing.image import ImageProcessor


def test_input_image_not_found(tmp_path):
    processor = ImageProcessor()

    with pytest.raises(FileNotFoundError):
        processor.process(
            str(tmp_path / "does_not_exist.jpg"),
            str(tmp_path / "output.jpg"),
        )


def test_image_resize(tmp_path):
    processor = ImageProcessor()

    input_file = tmp_path / "input.png"
    output_file = tmp_path / "output.jpg"

    image = Image.new("RGB", (1920, 1080), "white")
    image.save(input_file)

    result = processor.process(
        str(input_file),
        str(output_file),
    )

    assert result == str(output_file)
    assert output_file.exists()

    with Image.open(output_file) as processed:
        assert processed.size[0] <= 1280
        assert processed.size[1] <= 720
        assert processed.format == "JPEG"


def test_image_output_directory_created(tmp_path):
    processor = ImageProcessor()

    input_file = tmp_path / "input.png"
    output_file = tmp_path / "processed" / "output.jpg"

    image = Image.new("RGB", (800, 600), "white")
    image.save(input_file)

    result = processor.process(
        str(input_file),
        str(output_file),
    )

    assert result == str(output_file)
    assert output_file.exists()