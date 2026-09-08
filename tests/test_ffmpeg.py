from pathlib import Path

import pytest

from app.processing.ffmpeg import FFmpegProcessor


def test_input_video_not_found():
    processor = FFmpegProcessor()

    with pytest.raises(FileNotFoundError):
        processor.process_video(
            "does_not_exist.mp4",
            "output.mp4",
        )


def test_thumbnail_input_video_not_found():
    processor = FFmpegProcessor()

    with pytest.raises(FileNotFoundError):
        processor.extract_thumbnail(
            "does_not_exist.mp4",
            "thumbnail.jpg",
        )


def test_ffmpeg_failure(tmp_path):
    processor = FFmpegProcessor(
        ffmpeg_path="invalid-ffmpeg-command"
    )

    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake video")

    output_file = tmp_path / "output.mp4"

    with pytest.raises(RuntimeError, match="FFmpeg executable not found"):
        processor.process_video(
            str(input_file),
            str(output_file),
        )


def test_process_video_command(tmp_path, monkeypatch):
    processor = FFmpegProcessor()

    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake video")

    output_file = tmp_path / "optimized.mp4"

    def fake_run(command, capture_output, text):
        Path(command[-1]).write_bytes(b"processed video")

        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr(
        "app.processing.ffmpeg.subprocess.run",
        fake_run,
    )

    result = processor.process_video(
        str(input_file),
        str(output_file),
    )

    assert result == str(output_file)
    assert output_file.exists()


def test_extract_thumbnail(tmp_path, monkeypatch):
    processor = FFmpegProcessor()

    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake video")

    thumbnail_file = tmp_path / "thumbnail.jpg"

    def fake_run(command, capture_output, text):
        Path(command[-1]).write_bytes(b"fake jpeg")

        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr(
        "app.processing.ffmpeg.subprocess.run",
        fake_run,
    )

    result = processor.extract_thumbnail(
        str(input_file),
        str(thumbnail_file),
    )

    assert result == str(thumbnail_file)
    assert thumbnail_file.exists()


def test_process_creates_both_outputs(tmp_path, monkeypatch):
    processor = FFmpegProcessor()

    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake video")

    output_dir = tmp_path / "processed"

    def fake_run(command, capture_output, text):
        output_file = Path(command[-1])
        output_file.write_bytes(b"processed")

        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr(
        "app.processing.ffmpeg.subprocess.run",
        fake_run,
    )

    result = processor.process(
        str(input_file),
        str(output_dir),
    )

    assert result["video"] == str(output_dir / "optimized.mp4")
    assert result["thumbnail"] == str(output_dir / "thumbnail.jpg")

    assert (output_dir / "optimized.mp4").exists()
    assert (output_dir / "thumbnail.jpg").exists()