from PIL import Image, ImageDraw, ImageFont


SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


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
    """Compress and save an image to the specified output path."""

    if not 1 <= quality <= 100:
        raise ValueError("Quality must be between 1 and 100.")

    image.save(
        output_path,
        format=image.format or "JPEG",
        optimize=True,
        quality=quality,
    )


def add_watermark(
    image: Image.Image,
    text: str,
    output_path: str,
) -> None:
    """Add a text watermark to the bottom-right of an image."""

    if not text.strip():
        raise ValueError("Watermark text cannot be empty.")

    # Convert to RGBA so the watermark can support transparency.
    watermarked = image.convert("RGBA")

    draw = ImageDraw.Draw(watermarked)
    font = ImageFont.load_default()

    # Calculate watermark text dimensions.
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding = 10

    # Position watermark at the bottom-right.
    x = watermarked.width - text_width - padding
    y = watermarked.height - text_height - padding

    # Draw the watermark.
    draw.text(
        (x, y),
        text,
        font=font,
        fill=(255, 255, 255, 180),
    )

    watermarked.save(output_path)