from io import BytesIO

import pypdfium2 as pdfium
import pytesseract
from PIL import Image


class OCRParser:
    @staticmethod
    def parse(file_bytes: bytes, dpi: int = 220, max_pages: int = 3) -> str:
        pdf = pdfium.PdfDocument(BytesIO(file_bytes))
        page_count = min(len(pdf), max_pages)
        texts: list[str] = []

        for index in range(page_count):
            page = pdf[index]
            bitmap = page.render(scale=dpi / 72)
            pil_image = bitmap.to_pil()
            if not isinstance(pil_image, Image.Image):
                continue
            text = pytesseract.image_to_string(pil_image, lang="chi_sim+eng")
            texts.append(text)

        return "\n".join(texts).strip()
