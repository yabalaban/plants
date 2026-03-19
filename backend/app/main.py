import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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


os.makedirs("./photos", exist_ok=True)
app.mount("/photos", StaticFiles(directory="photos"), name="photos")

_frontend_dir = os.environ.get("PLANTS_FRONTEND_DIR", "../frontend/build")
if os.path.isdir(_frontend_dir):
    # Mount _app and static assets directly
    _app_dir = os.path.join(_frontend_dir, "_app")
    if os.path.isdir(_app_dir):
        app.mount("/_app", StaticFiles(directory=_app_dir), name="svelte_app")

    # SPA catch-all: serve static file if it exists, otherwise index.html
    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        file_path = os.path.join(_frontend_dir, path)
        if path and os.path.isfile(file_path):
            return FileResponse(file_path)
        index = os.path.join(_frontend_dir, "index.html")
        return FileResponse(index)
