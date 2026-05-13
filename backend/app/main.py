import uuid

from fastapi import FastAPI, File, Header, HTTPException, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api_errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.config import settings
from app.schemas import JobMatchRequest, JobMatchResponse, ResumeParseResult
from app.services.cache import CacheClient
from app.services.extractor import ResumeExtractor
from app.services.idempotency import (
    IdempotencyController,
    content_hash,
    normalize_idempotency_key,
    stable_hash,
)
from app.services.llm_extractor import LLMExtractor
from app.services.matcher import JobMatcher
from app.services.ocr import OCRParser
from app.services.pdf_parser import PDFParser
from app.services.text_processor import TextProcessor

app = FastAPI(title=settings.app_name)
cache = CacheClient(settings.redis_url)
idempotency = IdempotencyController(cache, ttl_seconds=settings.idempotency_ttl_seconds)


def _parse_cors_origins(value: str) -> list[str]:
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    return origins or ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(settings.cors_allow_origins),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Idempotency-Key", "X-Request-ID"],
    expose_headers=["X-Request-ID", "Idempotency-Replayed"],
)


app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/healthz")
def healthz() -> dict:
    cache_health = cache.health()
    return {"status": "ok" if cache_health["status"] == "ok" else "degraded", "cache": cache_health}


@app.post("/api/resume/upload", response_model=ResumeParseResult)
async def upload_resume(
    response: Response,
    file: UploadFile = File(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ResumeParseResult:
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF is supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded PDF is too large")

    digest = content_hash(content)
    request_hash = stable_hash(
        {
            "content_sha256": digest,
            "content_type": file.content_type,
            "filename": filename,
        }
    )
    key = normalize_idempotency_key(idempotency_key, settings.idempotency_key_max_length)
    idem_state = idempotency.begin("resume.upload", key, request_hash)
    if idem_state.should_replay:
        response.headers["Idempotency-Replayed"] = "true"
        return ResumeParseResult(**idem_state.response)

    try:
        existing = cache.get(f"resume-content:{digest}")
        if existing:
            cached = cache.get(f"resume:{existing['resume_id']}")
            if cached:
                result = ResumeParseResult(**cached)
                response.headers["Idempotency-Replayed"] = "true"
                idempotency.finish(idem_state, request_hash, result.model_dump())
                return result

        try:
            raw = PDFParser.parse(content)
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Failed to parse PDF") from exc

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
            filename=filename,
            raw_text=raw,
            cleaned_text=cleaned,
            extracted=extracted,
            extraction_method=extraction_method,
        )

        cache.set(f"resume:{resume_id}", result.model_dump())
        cache.set(f"resume-content:{digest}", {"resume_id": resume_id})
        idempotency.finish(idem_state, request_hash, result.model_dump())
        return result
    except Exception:
        idempotency.abort(idem_state)
        raise


@app.get("/api/resume/{resume_id}", response_model=ResumeParseResult)
def get_resume(resume_id: str) -> ResumeParseResult:
    data = cache.get(f"resume:{resume_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeParseResult(**data)


@app.post("/api/job/match", response_model=JobMatchResponse)
def match_job(
    http_response: Response,
    payload: JobMatchRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobMatchResponse:
    request_hash = stable_hash(payload.model_dump())
    key = normalize_idempotency_key(idempotency_key, settings.idempotency_key_max_length)
    idem_state = idempotency.begin("job.match", key, request_hash)
    if idem_state.should_replay:
        http_response.headers["Idempotency-Replayed"] = "true"
        return JobMatchResponse(**idem_state.response)

    data = cache.get(f"resume:{payload.resume_id}")
    if not data:
        idempotency.abort(idem_state)
        raise HTTPException(status_code=404, detail="Resume not found")

    try:
        match_key = f"match:{payload.resume_id}:{stable_hash({'jd_text': payload.jd_text})}"
        cached = cache.get(match_key)
        if cached:
            result = JobMatchResponse(**cached)
            http_response.headers["Idempotency-Replayed"] = "true"
            idempotency.finish(idem_state, request_hash, result.model_dump())
            return result

        resume = ResumeParseResult(**data)
        result = JobMatcher.match(resume, payload.jd_text)
        dumped = result.model_dump()
        cache.set(match_key, dumped)
        idempotency.finish(idem_state, request_hash, dumped)
        return result
    except Exception:
        idempotency.abort(idem_state)
        raise
