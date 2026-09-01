from pathlib import Path

from PIL import Image, UnidentifiedImageError


SUPPORTED_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}


class ImageProcessingError(Exception):
    """Base exception for image processing errors."""


def validate_image(image_path: str) -> Image.Image:
    """
    Validate and open an image.

    Raises:
        FileNotFoundError: If the image does not exist.
        ImageProcessingError: If the image is corrupted or unsupported.
    """
    path = Path(image_path)

    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        image = Image.open(path)
        image.verify()

        # Reopen after verify() because verify() invalidates the image object.
        image = Image.open(path)

    except (UnidentifiedImageError, OSError) as exc:
        raise ImageProcessingError(
            f"Invalid or corrupted image: {image_path}"
        ) from exc

    if image.format not in SUPPORTED_FORMATS:
        image.close()
        raise ImageProcessingError(
            f"Unsupported image format: {image.format}"
        )

    return image