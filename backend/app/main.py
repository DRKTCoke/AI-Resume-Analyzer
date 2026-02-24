import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import settings
from app.schemas import JobMatchRequest, ResumeParseResult
from app.services.cache import CacheClient
from app.services.extractor import ResumeExtractor
from app.services.llm_extractor import LLMExtractor
from app.services.matcher import JobMatcher
from app.services.ocr import OCRParser
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

    if settings.enable_ocr and TextProcessor.low_text_quality(raw):
        ocr_text = OCRParser.parse(content, dpi=settings.ocr_dpi, max_pages=settings.ocr_max_pages)
        if len(ocr_text) > len(raw):
            raw = ocr_text

    cleaned = TextProcessor.clean(raw)

    extraction_method = "rule"
    extracted = ResumeExtractor.extract(cleaned)

    if settings.enable_llm and settings.llm_api_key:
        llm_result = LLMExtractor.extract(
            text=cleaned,
            provider=settings.llm_provider,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
        )
        extracted = llm_result.extracted
        extraction_method = f"llm:{settings.llm_provider}"

    resume_id = str(uuid.uuid4())
    result = ResumeParseResult(
        resume_id=resume_id,
        filename=file.filename,
        raw_text=raw,
        cleaned_text=cleaned,
        extracted=extracted,
        extraction_method=extraction_method,
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
