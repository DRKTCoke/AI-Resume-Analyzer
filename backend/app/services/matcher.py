import re

from app.schemas import JobMatchResponse, MatchBreakdown, ResumeParseResult


EDU_RANK = {"大专": 1, "本科": 2, "硕士": 3, "博士": 4}


class JobMatcher:
    @staticmethod
    def _extract_jd_keywords(jd_text: str) -> list[str]:
        base = [
            "python",
            "java",
            "golang",
            "sql",
            "redis",
            "docker",
            "kubernetes",
            "fastapi",
            "微服务",
            "机器学习",
            "llm",
            "nlp",
            "算法",
        ]
        tokens = [k for k in base if k.lower() in jd_text.lower()]
        if tokens:
            return sorted(set(tokens))

        words = re.findall(r"[a-zA-Z]{3,}", jd_text.lower())
        return sorted(set(words))[:12]

    @staticmethod
    def _extract_required_education(jd_text: str) -> str | None:
        for edu in ["博士", "硕士", "本科", "大专"]:
            if edu in jd_text:
                return edu
        return None

    @staticmethod
    def _extract_required_years(jd_text: str) -> int | None:
        hit = re.search(r"(\d+)\+?\s*年", jd_text)
        return int(hit.group(1)) if hit else None

    @classmethod
    def match(cls, resume: ResumeParseResult, jd_text: str) -> JobMatchResponse:
        jd_keywords = cls._extract_jd_keywords(jd_text)
        resume_text = f"{resume.cleaned_text} {' '.join(resume.extracted.skills)}".lower()
        matched = [k for k in jd_keywords if k.lower() in resume_text]
        keyword_score = len(matched) / len(jd_keywords) if jd_keywords else 0.0

        exp_score = 0.5
        req_years = cls._extract_required_years(jd_text)
        if resume.extracted.years_of_experience:
            digits = re.findall(r"\d+", resume.extracted.years_of_experience)
            years = int(digits[0]) if digits else 0
            if req_years:
                exp_score = min(1.0, years / max(req_years, 1))
            else:
                exp_score = min(1.0, years / 5)

        edu_score = 0.5
        req_edu = cls._extract_required_education(jd_text)
        resume_edu = resume.extracted.education
        if req_edu and resume_edu:
            edu_score = 1.0 if EDU_RANK.get(resume_edu, 0) >= EDU_RANK.get(req_edu, 0) else 0.3
        elif req_edu and not resume_edu:
            edu_score = 0.2

        intent_score = 0.6
        if resume.extracted.intent:
            intent_score = 1.0 if any(k in resume.extracted.intent for k in matched) else 0.7

        total = round(keyword_score * 0.55 + exp_score * 0.25 + edu_score * 0.1 + intent_score * 0.1, 4)

        return JobMatchResponse(
            resume_id=resume.resume_id,
            total_score=total,
            breakdown=MatchBreakdown(
                jd_keywords=jd_keywords,
                matched_keywords=matched,
                keyword_match_rate=round(keyword_score, 4),
                experience_score=round(exp_score, 4),
                education_score=round(edu_score, 4),
                intent_score=round(intent_score, 4),
            ),
        )
