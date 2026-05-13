from app.schemas import ExtractedInfo, ResumeParseResult
from app.services.matcher import JobMatcher


def test_matcher_score_positive_with_stable_weights():
    resume = ResumeParseResult(
        resume_id="r1",
        filename="a.pdf",
        raw_text="",
        cleaned_text="5年工作经验，熟悉Python FastAPI Redis",
        extracted=ExtractedInfo(
            skills=["python", "fastapi", "redis"],
            years_of_experience="5年工作经验",
            education="本科",
            intent="后端开发工程师",
        ),
        extraction_method="rule",
    )

    result = JobMatcher.match(resume, "需要 Python FastAPI Redis，本科，3年经验")
    assert result.total_score > 0.75
    assert result.breakdown.education_score >= 1.0
    assert "python" in result.breakdown.matched_keywords
    assert result.analysis.match_level == "高匹配"
    assert result.analysis.strengths
    assert result.analysis.interview_focus


def test_matcher_generates_risks_and_suggestions_for_low_match():
    resume = ResumeParseResult(
        resume_id="r2",
        filename="b.pdf",
        raw_text="",
        cleaned_text="1年运营经验，熟悉活动策划",
        extracted=ExtractedInfo(
            skills=[],
            years_of_experience="1年经验",
            education="大专",
        ),
        extraction_method="rule",
    )

    result = JobMatcher.match(resume, "需要 Python Redis Docker Kubernetes，本科，3年经验")

    assert result.analysis.match_level == "低匹配"
    assert result.analysis.risks
    assert result.analysis.suggestions
    assert any("Python" in item or "python" in item for item in result.analysis.risks + result.analysis.suggestions)
