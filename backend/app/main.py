"""ScamShield API (FastAPI). Run from the backend folder:  uvicorn app.main:app --reload"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from . import config, db
from .api import router

log = logging.getLogger("scamshield")
app = FastAPI(title="ScamShield - Cyber Fraud Intelligence Desk", version="1.0",
              description="PS01 - scam message / phishing link / fake app / fraudulent website analysis (static analysis only).")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.on_event("startup")
def _startup():
    db.init()
    try:
        from .services import core
        core.warm_up()
    except Exception as e:  # keep the API up; the message endpoint will report the problem
        log.error("Could not load the message model: %s", e)


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error on %s", request.url.path)
    return JSONResponse({"detail": f"Server error: {type(exc).__name__}: {exc}"}, status_code=500)


# Built React app: copy frontend/dist/* into backend/static/ and it is served at http://localhost:8000/
_index = config.STATIC_DIR / "index.html"
if (config.STATIC_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=config.STATIC_DIR / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def home():
    if _index.exists():
        return FileResponse(_index)
    return JSONResponse({"service": "ScamShield API", "docs": "/docs",
                         "frontend": "Build the React app and copy frontend/dist/* into backend/static/ (see README)."})
