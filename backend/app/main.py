from fastapi import FastAPI

from app.db.database import create_db_and_tables

app = FastAPI(title="Study Quiz API")


@app.on_event("startup")
def startup() -> None:
    create_db_and_tables()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
