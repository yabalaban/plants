import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.routers import plants, settings_router
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    os.makedirs("./photos", exist_ok=True)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Plant Tracker", lifespan=lifespan)
app.include_router(plants.router)
app.include_router(settings_router.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


os.makedirs("./photos", exist_ok=True)
app.mount("/photos", StaticFiles(directory="photos"), name="photos")

_frontend_dir = os.environ.get("PLANTS_FRONTEND_DIR", "../frontend/build")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
