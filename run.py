import uvicorn

from app.config.settings import settings


def main() -> None:
    settings.load()
    uvicorn.run(
        "app.main:app",
        host=settings.data.server.host,
        port=settings.data.server.port,
        log_level=settings.data.server.log_level.lower(),
    )


if __name__ == "__main__":
    main()
