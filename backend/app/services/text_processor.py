import re


class TextProcessor:
    @staticmethod
    def clean(text: str) -> str:
        text = text.replace("\u3000", " ")
        text = re.sub(r"[\t\r]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        return text.strip()

    @staticmethod
    def low_text_quality(text: str) -> bool:
        clean = text.strip()
        if len(clean) < 80:
            return True
        alnum_count = len(re.findall(r"[A-Za-z0-9\u4e00-\u9fff]", clean))
        return alnum_count / max(1, len(clean)) < 0.35
