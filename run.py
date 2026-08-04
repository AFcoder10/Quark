import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from main import main as run_main


def main() -> None:
    run_main()


if __name__ == "__main__":
    main()
