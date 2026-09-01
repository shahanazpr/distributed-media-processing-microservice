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


def crop_image(
    image: Image.Image,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> Image.Image:
    """Crop an image using the provided coordinates."""
    if left < 0 or top < 0:
        raise ValueError("Crop coordinates cannot be negative.")

    if right <= left or bottom <= top:
        raise ValueError("Invalid crop coordinates.")

    if right > image.width or bottom > image.height:
        raise ValueError("Crop coordinates exceed image dimensions.")

    return image.crop((left, top, right, bottom))


def resize_image(
    image: Image.Image,
    width: int,
    height: int,
) -> Image.Image:
    """Resize an image to the requested dimensions."""
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be greater than zero.")

    return image.resize((width, height))