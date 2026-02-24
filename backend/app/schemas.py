from pydantic import BaseModel, Field


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


class JobMatchRequest(BaseModel):
    resume_id: str
    jd_text: str


class MatchBreakdown(BaseModel):
    jd_keywords: list[str]
    matched_keywords: list[str]
    keyword_match_rate: float
    experience_score: float


class JobMatchResponse(BaseModel):
    resume_id: str
    total_score: float
    breakdown: MatchBreakdown
