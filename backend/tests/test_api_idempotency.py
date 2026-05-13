from fastapi.testclient import TestClient

import app.main as main_module
from app.schemas import ExtractedInfo, JobMatchResponse, MatchBreakdown, ResumeParseResult
from app.services.cache import CacheClient
from app.services.idempotency import IdempotencyController


def make_client(monkeypatch):
    cache = CacheClient(None)
    monkeypatch.setattr(main_module, "cache", cache)
    monkeypatch.setattr(main_module, "idempotency", IdempotencyController(cache, ttl_seconds=60))
    monkeypatch.setattr(main_module.settings, "enable_ocr", False)
    monkeypatch.setattr(main_module.settings, "enable_llm", False)
    return TestClient(main_module.app), cache


def test_upload_deduplicates_same_pdf_content(monkeypatch):
    client, _ = make_client(monkeypatch)
    calls = {"parse": 0}

    def parse_pdf(content: bytes) -> str:
        calls["parse"] += 1
        return "Alice\n5 years Python FastAPI Redis alice@example.com"

    monkeypatch.setattr(main_module.PDFParser, "parse", staticmethod(parse_pdf))

    first = client.post(
        "/api/resume/upload",
        files={"file": ("alice.pdf", b"%PDF-1.4 same-content", "application/pdf")},
    )
    second = client.post(
        "/api/resume/upload",
        files={"file": ("alice.pdf", b"%PDF-1.4 same-content", "application/pdf")},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["resume_id"] == second.json()["resume_id"]
    assert calls["parse"] == 1


def test_upload_rejects_same_idempotency_key_with_different_content(monkeypatch):
    client, _ = make_client(monkeypatch)
    monkeypatch.setattr(main_module.PDFParser, "parse", staticmethod(lambda content: "Alice Python"))

    first = client.post(
        "/api/resume/upload",
        headers={"Idempotency-Key": "resume-upload-1"},
        files={"file": ("alice.pdf", b"%PDF-1.4 first", "application/pdf")},
    )
    second = client.post(
        "/api/resume/upload",
        headers={"Idempotency-Key": "resume-upload-1"},
        files={"file": ("alice.pdf", b"%PDF-1.4 second", "application/pdf")},
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_match_result_is_cached_by_resume_and_jd(monkeypatch):
    client, cache = make_client(monkeypatch)
    cache.set(
        "resume:r1",
        ResumeParseResult(
            resume_id="r1",
            filename="alice.pdf",
            raw_text="",
            cleaned_text="Alice Python Redis",
            extracted=ExtractedInfo(skills=["python", "redis"]),
            extraction_method="rule",
        ).model_dump(),
    )
    calls = {"match": 0}

    def match_resume(resume: ResumeParseResult, jd_text: str) -> JobMatchResponse:
        calls["match"] += 1
        return JobMatchResponse(
            resume_id=resume.resume_id,
            total_score=0.8 if "Redis" in jd_text else 0.6,
            breakdown=MatchBreakdown(
                jd_keywords=["python"],
                matched_keywords=["python"],
                keyword_match_rate=1.0,
                experience_score=0.5,
                education_score=0.5,
                intent_score=0.6,
            ),
        )

    monkeypatch.setattr(main_module.JobMatcher, "match", staticmethod(match_resume))

    payload = {"resume_id": "r1", "jd_text": "Need Python and Redis"}
    first = client.post("/api/job/match", json=payload)
    second = client.post("/api/job/match", json=payload)
    third = client.post("/api/job/match", json={"resume_id": "r1", "jd_text": "Need Python"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
    assert first.json() == second.json()
    assert calls["match"] == 2


def test_match_rejects_same_idempotency_key_with_different_payload(monkeypatch):
    client, cache = make_client(monkeypatch)
    cache.set(
        "resume:r1",
        ResumeParseResult(
            resume_id="r1",
            filename="alice.pdf",
            raw_text="",
            cleaned_text="Alice Python",
            extracted=ExtractedInfo(skills=["python"]),
            extraction_method="rule",
        ).model_dump(),
    )

    first = client.post(
        "/api/job/match",
        headers={"Idempotency-Key": "job-match-1"},
        json={"resume_id": "r1", "jd_text": "Need Python"},
    )
    second = client.post(
        "/api/job/match",
        headers={"Idempotency-Key": "job-match-1"},
        json={"resume_id": "r1", "jd_text": "Need Java"},
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_match_rejects_blank_jd(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.post("/api/job/match", json={"resume_id": "r1", "jd_text": "   "})

    assert response.status_code == 422


def test_request_id_is_echoed_on_success(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.get("/healthz", headers={"X-Request-ID": "trace-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "trace-123"


def test_error_response_has_stable_contract_and_request_id(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.get("/api/resume/missing", headers={"X-Request-ID": "trace-404"})

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "trace-404"
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Resume not found",
            "request_id": "trace-404",
        }
    }


def test_unknown_route_uses_error_contract(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.get("/missing-route", headers={"X-Request-ID": "trace-route-404"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["request_id"] == "trace-route-404"


def test_idempotency_replay_header_on_cached_match(monkeypatch):
    client, cache = make_client(monkeypatch)
    cache.set(
        "resume:r1",
        ResumeParseResult(
            resume_id="r1",
            filename="alice.pdf",
            raw_text="",
            cleaned_text="Alice Python",
            extracted=ExtractedInfo(skills=["python"]),
            extraction_method="rule",
        ).model_dump(),
    )

    first = client.post(
        "/api/job/match",
        headers={"Idempotency-Key": "same-match"},
        json={"resume_id": "r1", "jd_text": "Need Python"},
    )
    second = client.post(
        "/api/job/match",
        headers={"Idempotency-Key": "same-match"},
        json={"resume_id": "r1", "jd_text": "Need Python"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.headers["Idempotency-Replayed"] == "true"
