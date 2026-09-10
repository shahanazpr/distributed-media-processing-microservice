from pathlib import Path

from PIL import Image


class ImageProcessor:
    """Handles image processing using Pillow."""

    def process(
        self,
        input_path: str,
        output_path: str,
        size: tuple[int, int] = (1280, 720),
    ) -> str:
        """
        Resize an image and save it as JPEG.

        Args:
            input_path: Path to the input image.
            output_path: Path for the processed image.
            size: Target width and height.

        Returns:
            Path to the processed image.
        """
        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            raise FileNotFoundError(
                f"Input image not found: {input_file}"
            )

        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(input_file) as image:
                image = image.convert("RGB")
                image.thumbnail(size)
                image.save(output_file, format="JPEG", quality=85)

        except Exception as exc:
            raise RuntimeError(
                f"Image processing failed: {exc}"
            ) from exc

        if not output_file.exists():
            raise RuntimeError(
                "Image processing completed but output was not created."
            )

        return str(output_file)