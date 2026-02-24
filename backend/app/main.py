import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import settings
from app.schemas import JobMatchRequest, ResumeParseResult
from app.services.cache import CacheClient
from app.services.extractor import ResumeExtractor
from app.services.matcher import JobMatcher
from app.services.pdf_parser import PDFParser
from app.services.text_processor import TextProcessor

app = FastAPI(title=settings.app_name)
cache = CacheClient(settings.redis_url)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/api/resume/upload", response_model=ResumeParseResult)
async def upload_resume(file: UploadFile = File(...)) -> ResumeParseResult:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF is supported")

    content = await file.read()
    raw = PDFParser.parse(content)
    cleaned = TextProcessor.clean(raw)
    extracted = ResumeExtractor.extract(cleaned)

    resume_id = str(uuid.uuid4())
    result = ResumeParseResult(
        resume_id=resume_id,
        filename=file.filename,
        raw_text=raw,
        cleaned_text=cleaned,
        extracted=extracted,
    )

    cache.set(f"resume:{resume_id}", result.model_dump())
    return result


@app.get("/api/resume/{resume_id}", response_model=ResumeParseResult)
def get_resume(resume_id: str) -> ResumeParseResult:
    data = cache.get(f"resume:{resume_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeParseResult(**data)


@app.post("/api/job/match")
def match_job(payload: JobMatchRequest):
    data = cache.get(f"resume:{payload.resume_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume = ResumeParseResult(**data)
    response = JobMatcher.match(resume, payload.jd_text)
    cache.set(f"match:{payload.resume_id}", response.model_dump())
    return response
