from __future__ import annotations

import subprocess
from loguru import logger
from app.system.commands import FFMPEG, require_binary

_BEST_ENCODER: str | None = None
_HWACCEL_ARGS: list[str] | None = None


def get_hwaccel_args() -> list[str]:
    global _HWACCEL_ARGS
    if _HWACCEL_ARGS is not None:
        return _HWACCEL_ARGS

    ffmpeg = require_binary(FFMPEG)
    for hw in ["cuda", "d3d11va", "dxva2", "auto"]:
        cmd = [ffmpeg, "-y", "-hwaccel", hw, "-f", "lavfi", "-i", "testsrc=duration=1:size=640x360", "-f", "null", "-"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                logger.info("GPU Hardware Decoding detected: {}", hw)
                _HWACCEL_ARGS = ["-hwaccel", hw]
                return _HWACCEL_ARGS
        except Exception:
            pass

    _HWACCEL_ARGS = []
    return _HWACCEL_ARGS


def get_best_h264_encoder() -> str:
    global _BEST_ENCODER
    if _BEST_ENCODER is not None:
        return _BEST_ENCODER

    ffmpeg = require_binary(FFMPEG)
    candidates = [
        ("h264_nvenc", ["-preset", "p1", "-tune", "ll"]),
        ("h264_qsv", ["-preset", "veryfast"]),
        ("h264_amf", ["-usage", "lowlatency"]),
    ]

    for encoder, test_args in candidates:
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=1280x720:rate=30",
            "-c:v",
            encoder,
            *test_args,
            "-f",
            "null",
            "-",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                logger.info("GPU Hardware Encoder detected: {}", encoder)
                _BEST_ENCODER = encoder
                return encoder
        except Exception:
            pass

    logger.info("Using CPU H.264 Encoder: libx264")
    _BEST_ENCODER = "libx264"
    return "libx264"
