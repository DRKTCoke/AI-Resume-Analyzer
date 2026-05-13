from pydantic import BaseModel, Field, field_validator


class ExtractedInfo(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    years_of_experience: str | None = None
    education: str | None = None
    intent: str | None = None
    skills: list[str] = Field(default_factory=list)


class ResumeParseResult(BaseModel):
    resume_id: str
    filename: str
    raw_text: str
    cleaned_text: str
    extracted: ExtractedInfo
    extraction_method: str = "rule"


class JobMatchRequest(BaseModel):
    resume_id: str = Field(..., min_length=1, max_length=128)
    jd_text: str = Field(..., min_length=1, max_length=20000)

    @field_validator("resume_id", "jd_text")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class MatchBreakdown(BaseModel):
    jd_keywords: list[str]
    matched_keywords: list[str]
    keyword_match_rate: float
    experience_score: float
    education_score: float
    intent_score: float


class MatchAnalysis(BaseModel):
    match_level: str = "低匹配"
    summary: str = "匹配分析暂不可用"
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    interview_focus: list[str] = Field(default_factory=list)


class JobMatchResponse(BaseModel):
    resume_id: str
    total_score: float
    breakdown: MatchBreakdown
    analysis: MatchAnalysis = Field(default_factory=MatchAnalysis)


class LLMExtractionResult(BaseModel):
    extracted: ExtractedInfo
    raw_response: str
