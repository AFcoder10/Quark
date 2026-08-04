import argparse
import asyncio
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

BASE_DIR = Path(__file__).parent.resolve()
WEB_DIR = BASE_DIR / "web"
PORT = 8090
RESTART_MARKER = BASE_DIR / ".restart_request"

IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")


def free_port(port: int = PORT):
    try:
        if IS_WINDOWS:
            cmd = f'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :{port} ^| findstr LISTENING\') do taskkill /F /PID %a'
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif IS_LINUX:
            for pid in _port_pids(port):
                _kill_tree(pid)
    except Exception:
        pass


def _port_pids(port: int) -> list[int]:
    """PIDs of processes listening on the given port (cross-platform)."""
    pids: list[int] = []
    try:
        if IS_WINDOWS:
            out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=5)
            for line in out.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts and parts[-1].isdigit():
                        pids.append(int(parts[-1]))
        else:
            out = subprocess.run(["ss", "-ltnp"], capture_output=True, text=True, timeout=5)
            if out.returncode != 0:
                out = subprocess.run(["netstat", "-ltnp"], capture_output=True, text=True, timeout=5)
            pattern = re.compile(rf":{port}\s")
            for line in out.stdout.splitlines():
                if pattern.search(line) and "LISTEN" in line:
                    for chunk in line.split():
                        m = re.search(r"pid=(\d+)", chunk)
                        if m:
                            pids.append(int(m.group(1)))
        pids = list(dict.fromkeys(pids))
    except Exception:
        pass
    return pids


def kill_process_tree(pid: int):
    try:
        if IS_WINDOWS:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.killpg(pid, signal.SIGTERM)
            time.sleep(0.2)
            os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except Exception:
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass


def port_is_free(port: int = PORT) -> bool:
    return not _port_pids(port)


def code_snapshot() -> dict[str, int]:
    """mtime snapshot of all backend Python source files."""
    snap: dict[str, int] = {}
    targets = [BASE_DIR / "app", BASE_DIR / "main.py", BASE_DIR / "run.py"]
    for base in targets:
        if base.is_file():
            try:
                snap[str(base)] = base.stat().st_mtime_ns
            except OSError:
                pass
        elif base.is_dir():
            for p in base.rglob("*.py"):
                if "__pycache__" in p.parts:
                    continue
                try:
                    snap[str(p)] = p.stat().st_mtime_ns
                except OSError:
                    pass
    return snap


def _creation_flags():
    return subprocess.CREATE_NEW_CONSOLE if IS_WINDOWS else 0


def _spawn_kwargs():
    kwargs: dict = {"creationflags": _creation_flags()}
    if not IS_WINDOWS:
        kwargs["start_new_session"] = True
    return kwargs


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
        log_level=settings.data.server.log_level.lower(),
    )


def run_dev():
    print("🚀 Quark Supervisor running (this window stays open).")
    RESTART_MARKER.unlink(missing_ok=True)
    free_port(PORT)

    def spawn_backend():
        return subprocess.Popen(
            [sys.executable, str(BASE_DIR / "run.py")],
            cwd=str(BASE_DIR),
            **_spawn_kwargs(),
        )

    def spawn_frontend():
        return subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(WEB_DIR),
            shell=True,
            **_spawn_kwargs(),
        )

    backend = spawn_backend()
    frontend = spawn_frontend()
    print("✅ Backend + Frontend launched in separate terminals.")
    print("   • Watching backend source → closes & reopens the backend terminal.")
    print("   • Frontend keeps running (npm has its own hot reload).")
    print("   • Press Ctrl+C to stop everything.")

    last_snapshot = code_snapshot()

    try:
        while True:
            time.sleep(0.5)

            restart = False

            if RESTART_MARKER.exists():
                print("🔄 Restart requested by UI — closing backend terminal...")
                time.sleep(1.0)  # let the frontend receive the response
                RESTART_MARKER.unlink(missing_ok=True)
                restart = True

            if not restart:
                current = code_snapshot()
                if current != last_snapshot:
                    changed = [
                        p for p in set(current) | set(last_snapshot)
                        if current.get(p) != last_snapshot.get(p)
                    ]
                    last_snapshot = current
                    print("🔄 Backend source changed:")
                    for path in changed[:5]:
                        print(f"     {path}")
                    restart = True

            if restart:
                if backend.poll() is None:
                    kill_process_tree(backend.pid)
                for _ in range(80):
                    if port_is_free(PORT):
                        break
                    time.sleep(0.1)
                backend = spawn_backend()
                print("✅ Backend terminal reopened.")
                continue

            if backend.poll() is not None:
                print("⚠️  Backend exited unexpectedly — reopening...")
                backend = spawn_backend()
                continue

            if frontend.poll() is not None:
                print("⚠️  Frontend exited unexpectedly — reopening...")
                frontend = spawn_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all Quark servers...")
    finally:
        if backend.poll() is None:
            kill_process_tree(backend.pid)
        if frontend.poll() is None:
            kill_process_tree(frontend.pid)
        print("All servers stopped.")


def run_prod():
    print("🚀 Starting Quark Production Server...")

    dist_dir = WEB_DIR / "dist"
    if not dist_dir.exists() or not (dist_dir / "index.html").exists():
        print("Building web frontend...")
        subprocess.run(["npm", "run", "build"], cwd=str(WEB_DIR), shell=True, check=True)

    run_backend()


def main():
    parser = argparse.ArgumentParser(description="Quark Media Server Runner")
    parser.add_argument("--backend", action="store_true", help="Run backend server only in current terminal")
    parser.add_argument("--frontend", action="store_true", help="Run frontend dev server only in current terminal")
    parser.add_argument("--prod", action="store_true", help="Run in production mode (serves static build)")
    args = parser.parse_args()

    if args.backend:
        run_backend()
    elif args.frontend:
        subprocess.run(["npm", "run", "dev"], cwd=str(WEB_DIR), shell=True)
    elif args.prod:
        run_prod()
    else:
        run_dev()


if __name__ == "__main__":
    main()
