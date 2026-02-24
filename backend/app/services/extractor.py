import re

from app.schemas import ExtractedInfo


COMMON_SKILLS = [
    "python",
    "java",
    "golang",
    "sql",
    "redis",
    "docker",
    "kubernetes",
    "fastapi",
    "flask",
    "django",
    "机器学习",
    "深度学习",
    "nlp",
    "llm",
]


class ResumeExtractor:
    @staticmethod
    def extract(text: str) -> ExtractedInfo:
        phone = re.search(r"(?<!\d)(1[3-9]\d{9})(?!\d)", text)
        email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        years = re.search(r"(\d+\+?\s*年(?:工作)?经验)", text)

        name = None
        first_line = text.splitlines()[0] if text.splitlines() else ""
        if 1 <= len(first_line.strip()) <= 10:
            name = first_line.strip()

        skills = [s for s in COMMON_SKILLS if s.lower() in text.lower()]

        edu = None
        for token in ["博士", "硕士", "本科", "大专"]:
            if token in text:
                edu = token
                break

        address = None
        for key in ["上海", "北京", "深圳", "广州", "杭州", "成都", "武汉", "南京"]:
            if key in text:
                address = key
                break

        intent = None
        intent_match = re.search(r"(求职意向[:：].*)", text)
        if intent_match:
            intent = intent_match.group(1)

        return ExtractedInfo(
            name=name,
            phone=phone.group(1) if phone else None,
            email=email.group(0) if email else None,
            address=address,
            years_of_experience=years.group(1) if years else None,
            education=edu,
            intent=intent,
            skills=skills,
        )
