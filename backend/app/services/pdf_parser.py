from io import BytesIO

from pypdf import PdfReader


class PDFParser:
    @staticmethod
    def parse(file_bytes: bytes) -> str:
        reader = PdfReader(BytesIO(file_bytes))
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return "\n".join(texts)
