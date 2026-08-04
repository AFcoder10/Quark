import asyncio
import subprocess
import sys
from app.config.settings import settings
import uvicorn

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def _free_port(port: int) -> None:
    if sys.platform != "win32":
        return
    try:
        cmd = (
            f'for /f "tokens=5" %a in '
            f"('netstat -aon ^| findstr :{port} ^| findstr LISTENING') do taskkill /F /PID %a"
        )
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def main() -> None:
    settings.load()
    _free_port(settings.data.server.port)
    uvicorn.run(
        "app.main:app",
        host=settings.data.server.host,
        port=settings.data.server.port,
        log_level=settings.data.server.log_level.lower(),
    )


if __name__ == "__main__":
    main()
