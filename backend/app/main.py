from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.routers import plants, settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Plant Tracker", lifespan=lifespan)
app.include_router(plants.router)
app.include_router(settings_router.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
