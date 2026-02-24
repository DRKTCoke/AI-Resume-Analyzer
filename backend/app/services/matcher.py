import re

from app.schemas import JobMatchResponse, MatchBreakdown, ResumeParseResult


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
        if not tokens:
            words = re.findall(r"[a-zA-Z]{3,}", jd_text.lower())
            tokens = sorted(set(words))[:10]
        return tokens

    @classmethod
    def match(cls, resume: ResumeParseResult, jd_text: str) -> JobMatchResponse:
        jd_keywords = cls._extract_jd_keywords(jd_text)
        resume_text = f"{resume.cleaned_text} {' '.join(resume.extracted.skills)}".lower()
        matched = [k for k in jd_keywords if k.lower() in resume_text]

        keyword_score = len(matched) / len(jd_keywords) if jd_keywords else 0.0

        exp_score = 0.6
        if resume.extracted.years_of_experience:
            digits = re.findall(r"\d+", resume.extracted.years_of_experience)
            years = int(digits[0]) if digits else 0
            exp_score = min(1.0, years / 5)

        total = round(keyword_score * 0.7 + exp_score * 0.3, 4)

        return JobMatchResponse(
            resume_id=resume.resume_id,
            total_score=total,
            breakdown=MatchBreakdown(
                jd_keywords=jd_keywords,
                matched_keywords=matched,
                keyword_match_rate=round(keyword_score, 4),
                experience_score=round(exp_score, 4),
            ),
        )
