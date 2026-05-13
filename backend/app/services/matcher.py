import re

from app.schemas import JobMatchResponse, MatchAnalysis, MatchBreakdown, ResumeParseResult


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

    @staticmethod
    def _extract_resume_years(resume: ResumeParseResult) -> int | None:
        if not resume.extracted.years_of_experience:
            return None
        digits = re.findall(r"\d+", resume.extracted.years_of_experience)
        return int(digits[0]) if digits else None

    @staticmethod
    def _match_level(total_score: float) -> str:
        if total_score >= 0.8:
            return "高匹配"
        if total_score >= 0.6:
            return "中匹配"
        return "低匹配"

    @classmethod
    def _build_analysis(
        cls,
        resume: ResumeParseResult,
        total_score: float,
        jd_keywords: list[str],
        matched: list[str],
        keyword_score: float,
        exp_score: float,
        edu_score: float,
        intent_score: float,
        req_years: int | None,
        resume_years: int | None,
        req_edu: str | None,
    ) -> MatchAnalysis:
        missing = [k for k in jd_keywords if k not in matched]
        level = cls._match_level(total_score)
        strengths: list[str] = []
        risks: list[str] = []
        suggestions: list[str] = []
        interview_focus: list[str] = []

        if matched:
            strengths.append(f"已命中岗位关键词：{'、'.join(matched[:6])}")
            interview_focus.append(f"请展开说明一个使用 {matched[0]} 解决实际问题的项目。")
        if keyword_score >= 0.8 and jd_keywords:
            strengths.append("核心技能与岗位描述高度重合，具备较好的初筛优势。")
        if req_years and resume_years is not None and resume_years >= req_years:
            strengths.append(f"工作年限满足岗位要求，简历体现约 {resume_years} 年相关经验。")
        if edu_score >= 1.0 and req_edu:
            strengths.append(f"学历背景满足岗位要求：{req_edu}。")
        if intent_score >= 0.9:
            strengths.append("求职意向与岗位关键词存在直接关联。")
        if not strengths:
            strengths.append("简历已提供基础信息，可作为初筛参考。")

        if missing:
            risks.append(f"JD 中仍有未体现的关键词：{'、'.join(missing[:6])}")
            suggestions.append(f"补充与 {'、'.join(missing[:3])} 相关的项目经历、职责或成果。")
            interview_focus.append(f"请说明你对 {missing[0]} 的理解，以及是否有相关实践。")
        if req_years and resume_years is None:
            risks.append(f"JD 要求约 {req_years} 年经验，但简历未明确展示工作年限。")
            suggestions.append("在简历概要或经历标题中明确标注相关工作年限。")
        elif req_years and resume_years is not None and resume_years < req_years:
            risks.append(f"岗位要求约 {req_years} 年经验，简历当前体现约 {resume_years} 年。")
            suggestions.append("突出与目标岗位最相关的项目深度，用成果质量弥补年限差距。")
        if req_edu and edu_score < 1.0:
            risks.append(f"学历信息与岗位要求 {req_edu} 存在差距或未充分体现。")
            suggestions.append("补充专业背景、证书、课程或项目成果来增强岗位相关性。")
        if keyword_score < 0.5 and jd_keywords:
            suggestions.append("将 JD 中高频硬技能映射到简历技能栈和项目描述中，避免只写泛化职责。")
        if not resume.extracted.intent:
            risks.append("简历缺少明确求职意向，岗位方向判断依据较弱。")
            suggestions.append("增加一句目标岗位或职业方向，帮助招聘方快速建立匹配判断。")
        if not risks:
            risks.append("暂未发现明显硬性缺口，建议重点核验项目真实性和深度。")
        if not suggestions:
            suggestions.append("可继续补充量化成果，例如性能提升、成本下降、转化率或交付规模。")

        interview_focus.append("过往经历中与该岗位要求最接近的项目是什么？你负责了哪一部分？")
        if exp_score < 1.0:
            interview_focus.append("如果入职该岗位，你会如何快速补齐当前经验或技能缺口？")

        summary = f"{level}，总分 {total_score:.2f}。"
        if matched and jd_keywords:
            summary += f" 已命中 {len(matched)}/{len(jd_keywords)} 个岗位关键词。"
        elif jd_keywords:
            summary += " 岗位关键词命中较少，需要进一步补充相关经历。"
        else:
            summary += " JD 可识别关键词较少，建议补充更完整的岗位描述后复评。"

        return MatchAnalysis(
            match_level=level,
            summary=summary,
            strengths=strengths[:5],
            risks=risks[:5],
            suggestions=suggestions[:5],
            interview_focus=interview_focus[:4],
        )

    @classmethod
    def match(cls, resume: ResumeParseResult, jd_text: str) -> JobMatchResponse:
        jd_keywords = cls._extract_jd_keywords(jd_text)
        resume_text = f"{resume.cleaned_text} {' '.join(resume.extracted.skills)}".lower()
        matched = [k for k in jd_keywords if k.lower() in resume_text]
        keyword_score = len(matched) / len(jd_keywords) if jd_keywords else 0.0

        exp_score = 0.5
        req_years = cls._extract_required_years(jd_text)
        resume_years = cls._extract_resume_years(resume)
        if resume_years is not None:
            if req_years:
                exp_score = min(1.0, resume_years / max(req_years, 1))
            else:
                exp_score = min(1.0, resume_years / 5)

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
            analysis=cls._build_analysis(
                resume=resume,
                total_score=total,
                jd_keywords=jd_keywords,
                matched=matched,
                keyword_score=keyword_score,
                exp_score=exp_score,
                edu_score=edu_score,
                intent_score=intent_score,
                req_years=req_years,
                resume_years=resume_years,
                req_edu=req_edu,
            ),
        )
