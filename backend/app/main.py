from fastapi import FastAPI

app = FastAPI(title="Plant Tracker")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
