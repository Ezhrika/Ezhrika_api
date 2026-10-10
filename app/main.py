from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(title=settings.app_name, debug=settings.debug)


@app.get("/", tags=["service"])
def health() -> dict[str, str]:
    return {"status": "ok"}
