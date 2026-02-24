import re


class TextProcessor:
    @staticmethod
    def clean(text: str) -> str:
        text = text.replace("\u3000", " ")
        text = re.sub(r"[\t\r]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        return text.strip()
