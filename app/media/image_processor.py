from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}

SUPPORTED_WATERMARK_POSITIONS = {
    "top-left",
    "top-right",
    "bottom-left",
    "bottom-right",
    "center",
}


def validate_image(image_path: str) -> Image.Image:
    """Load and validate an image file."""

    try:
        image = Image.open(image_path)
        image.verify()

        # Reopen after verify() because verify() invalidates the image object.
        image = Image.open(image_path)

        if image.format not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported image format: {image.format}"
            )

        return image

    except ValueError:
        raise
    except (OSError, Image.UnidentifiedImageError) as exc:
        raise ValueError("Invalid or corrupted image file.") from exc


def crop_image(
    image: Image.Image,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> Image.Image:
    """Crop an image using the specified coordinates."""

    if left < 0 or top < 0:
        raise ValueError("Crop coordinates cannot be negative.")

    if right <= left or bottom <= top:
        raise ValueError("Invalid crop dimensions.")

    if right > image.width or bottom > image.height:
        raise ValueError("Crop coordinates exceed image dimensions.")

    return image.crop((left, top, right, bottom))


def resize_image(
    image: Image.Image,
    width: int,
    height: int,
) -> Image.Image:
    """Resize an image to the specified dimensions."""

    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be greater than zero.")

    return image.resize((width, height))


def compress_image(
    image: Image.Image,
    output_path: str,
    quality: int = 85,
) -> None:
    """Compress and save the image to the specified output path."""

    if not 1 <= quality <= 100:
        raise ValueError("Quality must be between 1 and 100.")

    image.save(
        output_path,
        format=image.format or "JPEG",
        optimize=True,
        quality=quality,
    )


def _calculate_position(
    base_size: tuple[int, int],
    watermark_size: tuple[int, int],
    position: str,
    padding: int = 10,
) -> tuple[int, int]:
    """Calculate the watermark position."""

    base_width, base_height = base_size
    watermark_width, watermark_height = watermark_size

    if position not in SUPPORTED_WATERMARK_POSITIONS:
        raise ValueError(
            "Invalid watermark position. "
            f"Supported positions: {sorted(SUPPORTED_WATERMARK_POSITIONS)}"
        )

    if position == "top-left":
        return padding, padding

    if position == "top-right":
        return (
            base_width - watermark_width - padding,
            padding,
        )

    if position == "bottom-left":
        return (
            padding,
            base_height - watermark_height - padding,
        )

    if position == "center":
        return (
            (base_width - watermark_width) // 2,
            (base_height - watermark_height) // 2,
        )

    return (
        base_width - watermark_width - padding,
        base_height - watermark_height - padding,
    )


def _apply_opacity(
    watermark: Image.Image,
    opacity: float,
) -> Image.Image:
    """Apply opacity to a watermark image."""

    if not 0.0 <= opacity <= 1.0:
        raise ValueError("Watermark opacity must be between 0 and 1.")

    watermark = watermark.convert("RGBA")

    alpha = watermark.getchannel("A")
    alpha = alpha.point(lambda value: int(value * opacity))

    watermark.putalpha(alpha)

    return watermark


def add_watermark(
    image: Image.Image,
    text: str,
    output_path: str,
    position: str = "bottom-right",
    opacity: float = 0.7,
    watermark_path: str | None = None,
) -> None:
    """
    Add a text or image watermark to an image.

    Args:
        image: Source image.
        text: Text watermark. Required when watermark_path is not supplied.
        output_path: Destination image path.
        position: Watermark position.
        opacity: Watermark opacity between 0 and 1.
        watermark_path: Optional path to a watermark image.

    Raises:
        ValueError: If watermark settings or assets are invalid.
        FileNotFoundError: If the watermark image does not exist.
    """

    if not 0.0 <= opacity <= 1.0:
        raise ValueError("Watermark opacity must be between 0 and 1.")

    if position not in SUPPORTED_WATERMARK_POSITIONS:
        raise ValueError(
            "Invalid watermark position. "
            f"Supported positions: {sorted(SUPPORTED_WATERMARK_POSITIONS)}"
        )

    watermarked = image.convert("RGBA")

    if watermark_path:
        watermark_file = Path(watermark_path)

        if not watermark_file.exists():
            raise FileNotFoundError(
                f"Watermark asset not found: {watermark_file}"
            )

        try:
            with Image.open(watermark_file) as watermark_image:
                watermark = watermark_image.convert("RGBA")

                watermark = _apply_opacity(
                    watermark,
                    opacity,
                )

                # Prevent a very large watermark from covering the image.
                max_width = max(1, watermarked.width // 3)
                max_height = max(1, watermarked.height // 3)

                watermark.thumbnail(
                    (max_width, max_height),
                    Image.Resampling.LANCZOS,
                )

                x, y = _calculate_position(
                    watermarked.size,
                    watermark.size,
                    position,
                )

                watermarked.alpha_composite(
                    watermark,
                    (x, y),
                )

        except FileNotFoundError:
            raise
        except (OSError, Image.UnidentifiedImageError) as exc:
            raise ValueError(
                f"Invalid watermark asset: {watermark_file}"
            ) from exc

    else:
        if not text.strip():
            raise ValueError("Watermark text cannot be empty.")

        draw = ImageDraw.Draw(watermarked)
        font = ImageFont.load_default()

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=font,
        )

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x, y = _calculate_position(
            watermarked.size,
            (text_width, text_height),
            position,
        )

        draw.text(
            (x, y),
            text,
            font=font,
            fill=(255, 255, 255, int(255 * opacity)),
        )

    output_file = Path(output_path)
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    watermarked.save(output_file)