from fastapi import APIRouter, FastAPI

app = FastAPI(title="BAC Tracker API", version="0.1.0")

api = APIRouter(prefix="/api/v1")


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api)
