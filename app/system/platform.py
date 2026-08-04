from __future__ import annotations

import platform
import sys


PLATFORM = sys.platform


def is_windows() -> bool:
    return sys.platform.startswith("win")


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def platform_name() -> str:
    return f"{platform.system()} {platform.release()}"