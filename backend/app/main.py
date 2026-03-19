from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.routers import plants, settings_router
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Plant Tracker", lifespan=lifespan)
app.include_router(plants.router)
app.include_router(settings_router.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
