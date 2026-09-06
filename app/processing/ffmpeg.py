import subprocess
import tempfile
from pathlib import Path


class FFmpegProcessor:
    """Handles video processing using FFmpeg."""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def _run_ffmpeg(self, command: list[str]) -> None:
        """Run an FFmpeg command and handle execution failures."""

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"FFmpeg executable not found: {self.ffmpeg_path}"
            ) from exc

        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg processing failed:\n{result.stderr}"
            )

    def process_video(
        self,
        input_path: str,
        output_path: str,
        resolution: str = "1280:720",
    ) -> str:
        """
        Transcode a video to an optimized H.264 MP4 file.

        Args:
            input_path: Path to the input video.
            output_path: Path for the processed MP4.
            resolution: Output resolution in WIDTH:HEIGHT format.

        Returns:
            Path to the processed video.

        Raises:
            FileNotFoundError: If the input video does not exist.
            RuntimeError: If FFmpeg processing fails.
        """

        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            raise FileNotFoundError(
                f"Input video not found: {input_file}"
            )

        output_file.parent.mkdir(parents=True, exist_ok=True)

        command = [
            self.ffmpeg_path,
            "-i",
            str(input_file),
            "-vf",
            f"scale={resolution}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            "-y",
            str(output_file),
        ]

        self._run_ffmpeg(command)

        if not output_file.exists():
            raise RuntimeError(
                "FFmpeg completed successfully but output video was not created."
            )

        return str(output_file)

    def extract_thumbnail(
        self,
        input_path: str,
        output_path: str,
        timestamp: str = "00:00:01",
    ) -> str:
        """
        Extract a JPEG thumbnail from a video.

        Args:
            input_path: Path to the input video.
            output_path: Path for the thumbnail.
            timestamp: Timestamp from which to extract the thumbnail.

        Returns:
            Path to the generated thumbnail.
        """

        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            raise FileNotFoundError(
                f"Input video not found: {input_file}"
            )

        output_file.parent.mkdir(parents=True, exist_ok=True)

        command = [
            self.ffmpeg_path,
            "-ss",
            timestamp,
            "-i",
            str(input_file),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            "-y",
            str(output_file),
        ]

        self._run_ffmpeg(command)

        if not output_file.exists():
            raise RuntimeError(
                "FFmpeg completed successfully but thumbnail was not created."
            )

        return str(output_file)

    def process(
        self,
        input_path: str,
        output_dir: str | None = None,
        resolution: str = "1280:720",
    ) -> dict[str, str]:
        """
        Process a video and generate both required outputs.

        Outputs:
            optimized.mp4
            thumbnail.jpg

        If output_dir is not supplied, a temporary directory is created.
        The caller is responsible for cleaning up the temporary directory.
        """

        input_file = Path(input_path)

        if not input_file.exists():
            raise FileNotFoundError(
                f"Input video not found: {input_file}"
            )

        if output_dir is not None:
            output_directory = Path(output_dir)
            output_directory.mkdir(parents=True, exist_ok=True)
        else:
            temp_dir = tempfile.mkdtemp(
                prefix="ffmpeg_processing_"
            )
            output_directory = Path(temp_dir)

        optimized_path = output_directory / "optimized.mp4"
        thumbnail_path = output_directory / "thumbnail.jpg"

        self.process_video(
            str(input_file),
            str(optimized_path),
            resolution,
        )

        self.extract_thumbnail(
            str(input_file),
            str(thumbnail_path),
        )

        return {
            "video": str(optimized_path),
            "thumbnail": str(thumbnail_path),
        }