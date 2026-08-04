import argparse
import asyncio
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

BASE_DIR = Path(__file__).parent.resolve()
WEB_DIR = BASE_DIR / "web"


def run_backend():
    import asyncio
    from app.config.settings import settings
    import uvicorn

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    settings.load()
    uvicorn.run(
        "app.main:app",
        host=settings.data.server.host,
        port=settings.data.server.port,
        reload=True,
        reload_dirs=["app"],
        log_level=settings.data.server.log_level.lower(),
        loop="asyncio",
    )


def run_dev():
    print("🚀 Starting Quark Server (Hot-Reload Backend + Frontend Dev HMR)...")

    # 1. Start Backend process
    backend_cmd = [sys.executable, "-c", "import main; main.run_backend()"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(BASE_DIR))

    # 2. Start Frontend Vite Dev Server
    frontend_cmd = ["npm", "run", "dev"]
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(WEB_DIR), shell=True)

    try:
        while True:
            time.sleep(0.5)
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\nStopping Quark development servers...")
    finally:
        for proc in (backend_proc, frontend_proc):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass


def run_prod():
    print("🚀 Starting Quark Production Server...")

    dist_dir = WEB_DIR / "dist"
    if not dist_dir.exists() or not (dist_dir / "index.html").exists():
        print("Building web frontend...")
        subprocess.run(["npm", "run", "build"], cwd=str(WEB_DIR), shell=True, check=True)

    run_backend()


def main():
    parser = argparse.ArgumentParser(description="Quark Media Server Runner")
    parser.add_argument("--prod", action="store_true", help="Run in production mode (serves static build)")
    args = parser.parse_args()

    if args.prod:
        run_prod()
    else:
        run_dev()


if __name__ == "__main__":
    main()
