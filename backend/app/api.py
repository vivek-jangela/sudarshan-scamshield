"""All REST routes under /api. Routes are plain `def` so FastAPI runs the (blocking) analysis in its thread pool."""
import os
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response, HTMLResponse
from . import config, db
from .schemas import MessageIn, UrlIn, WebsiteIn, AssistantIn, StatusIn
from .services import analysis, similarity, reports, assistant
from .services.analysis import AnalysisError

router = APIRouter(prefix="/api")


def _guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except AnalysisError as e:
        raise HTTPException(400, str(e))


# ---------------------------------------------------------------- analysis
@router.post("/analyze/message")
def analyze_message(b: MessageIn):
    return _guard(analysis.analyze_message, b.text, b.reporter, b.channel)


@router.post("/analyze/url")
def analyze_url(b: UrlIn):
    return _guard(analysis.analyze_url, b.url, b.reporter)


@router.post("/analyze/website")
def analyze_website(b: WebsiteIn):
    return _guard(analysis.analyze_website, b.html, b.url, b.reporter)


@router.post("/analyze/apk")
def analyze_apk(file: UploadFile = File(...), reporter: str = Form("officer")):
    limit = config.MAX_APK_MB * 1024 * 1024
    fd, path = tempfile.mkstemp(suffix=".apk")
    try:
        size = 0
        with os.fdopen(fd, "wb") as out:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, f"APK is larger than {config.MAX_APK_MB} MB.")
                out.write(chunk)
        if size == 0:
            raise HTTPException(400, "The uploaded file is empty.")
        return _guard(analysis.analyze_apk_file, path, file.filename or "upload.apk", reporter)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


@router.post("/analyze/store-link")
def analyze_store(link: str = Form(...), reporter: str = Form("citizen")):
    return _guard(analysis.analyze_store_link, link, reporter)


@router.get("/check")
def check(url: str = Query(..., min_length=3)):
    """Warn-before-open check used by the Link safety page, and by a browser extension or chat bot."""
    return _guard(analysis.check_link, url)


# ---------------------------------------------------------------- cases
@router.get("/cases")
def list_cases(q: str = "", level: str = "", kind: str = ""):
    return db.list_cases(q, level, kind)


@router.get("/cases/{cid}")
def get_case(cid: int):
    c = db.get_case(cid)
    if not c:
        raise HTTPException(404, "Case not found")
    return c


@router.get("/cases/{cid}/links")
def case_links(cid: int):
    if not db.get_case(cid):
        raise HTTPException(404, "Case not found")
    return db.links(cid)


@router.get("/cases/{cid}/similar")
def case_similar(cid: int):
    if not db.get_case(cid):
        raise HTTPException(404, "Case not found")
    return similarity.similar_cases(cid)


@router.post("/cases/{cid}/status")
def case_status(cid: int, b: StatusIn):
    if b.status not in ("new", "under_review", "escalated", "closed"):
        raise HTTPException(400, "status must be new, under_review, escalated or closed")
    if not db.get_case(cid):
        raise HTTPException(404, "Case not found")
    db.set_status(cid, b.status)
    return {"ok": True}


@router.get("/cases/{cid}/report")
def case_report(cid: int, format: str = "html"):
    c = db.get_case(cid)
    if not c:
        raise HTTPException(404, "Case not found")
    if format == "pdf":
        return Response(reports.case_pdf(c), media_type="application/pdf",
                        headers={"Content-Disposition": f'inline; filename="scamshield_case_{cid}.pdf"'})
    if format == "json":
        return c
    return HTMLResponse(reports.case_html(c))


# ---------------------------------------------------------------- intelligence
@router.get("/heatlist")
def heatlist(type: str = ""):
    return db.heatlist(type)


@router.get("/graph")
def graph():
    return db.graph()


@router.get("/stats")
def stats():
    return db.stats()


@router.post("/assistant")
def ask(b: AssistantIn):
    try:
        return assistant.answer(b.question, b.case_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/health")
def health():
    return {"status": "ok", "deep_checks": config.DEEP_CHECKS, "llm_assistant": bool(config.ANTHROPIC_API_KEY)}
