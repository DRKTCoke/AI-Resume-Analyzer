from app.schemas import ExtractedInfo, ResumeParseResult
from app.services.matcher import JobMatcher


def test_matcher_score_positive():
    resume = ResumeParseResult(
        resume_id="r1",
        filename="a.pdf",
        raw_text="",
        cleaned_text="5年工作经验，熟悉Python FastAPI Redis",
        extracted=ExtractedInfo(skills=["python", "fastapi", "redis"], years_of_experience="5年工作经验"),
    )

    result = JobMatcher.match(resume, "需要 Python FastAPI Redis 开发经验")
    assert result.total_score > 0.7
    assert "python" in result.breakdown.matched_keywords
