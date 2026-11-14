import os
import logging
from typing import List, Dict, Any
import fitz  # PyMuPDF
import docx

logger = logging.getLogger(__name__)


class ParsedPage:
    def __init__(self, page_number: int, text: str, word_count: int = 0):
        self.page_number = page_number
        self.text = text
        self.word_count = word_count or len(text.split())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_number": self.page_number,
            "text": self.text,
            "word_count": self.word_count,
        }


class DocumentParser:
    """Multi-format document parsing engine supporting PDF, DOCX, and TXT."""

    @staticmethod
    def parse_pdf(file_path: str) -> List[ParsedPage]:
        pages = []
        doc = fitz.open(file_path)
        try:
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                text = page.get_text("text").strip()
                page_num = page_idx + 1

                # If text is empty or very short, check for image OCR
                if len(text) < 20:
                    text_extracted = DocumentParser._attempt_ocr_or_fallback(page, page_num)
                    if text_extracted:
                        text = text_extracted

                pages.append(ParsedPage(page_number=page_num, text=text))
        finally:
            doc.close()
        return pages

    @staticmethod
    def _attempt_ocr_or_fallback(page: fitz.Page, page_num: int) -> str:
        """OCR fallback for scanned PDF documents if tesseract is available."""
        try:
            import pytesseract
            from PIL import Image
            import io

            pix = page.get_pixmap(dpi=150)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text = pytesseract.image_to_string(img).strip()
            if ocr_text:
                return ocr_text
        except Exception as e:
            logger.debug(f"OCR not applied for page {page_num}: {e}")
        return f"[Scanned page {page_num} image content]"

    @staticmethod
    def parse_docx(file_path: str) -> List[ParsedPage]:
        doc = docx.Document(file_path)
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        # Estimate pages based on paragraph chunks (approx 500 words per page)
        words = full_text.split()
        if not words:
            return [ParsedPage(page_number=1, text="")]

        chunk_size = 500
        pages = []
        for i in range(0, len(words), chunk_size):
            page_text = " ".join(words[i : i + chunk_size])
            pages.append(ParsedPage(page_number=len(pages) + 1, text=page_text))
        return pages

    @staticmethod
    def parse_txt(file_path: str) -> List[ParsedPage]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        words = content.split()
        if not words:
            return [ParsedPage(page_number=1, text="")]

        chunk_size = 600
        pages = []
        for i in range(0, len(words), chunk_size):
            page_text = " ".join(words[i : i + chunk_size])
            pages.append(ParsedPage(page_number=len(pages) + 1, text=page_text))
        return pages

    @classmethod
    def parse_document(cls, file_path: str, filename: str) -> List[ParsedPage]:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return cls.parse_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return cls.parse_docx(file_path)
        elif ext in [".txt", ".csv", ".json"]:
            return cls.parse_txt(file_path)
        else:
            # Fallback to plain text read
            return cls.parse_txt(file_path)

