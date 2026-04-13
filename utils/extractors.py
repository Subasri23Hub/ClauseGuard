"""
extractors.py — Extract plain text from PDFs and images.

PDF  → PyMuPDF (fitz)
Image → pytesseract (Tesseract OCR)

Setup note:
  Tesseract must be installed on your system:
    macOS:   brew install tesseract
    Ubuntu:  sudo apt install tesseract-ocr
    Windows: https://github.com/UB-Mannheim/tesseract/wiki
"""

import io
from typing import Tuple

# ── PDF extraction ──────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, str]:
    """
    Extract text from a PDF file's bytes.
    Returns (extracted_text, error_message).
    error_message is empty string on success.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return "", "PyMuPDF is not installed. Run: pip install PyMuPDF"

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            pages_text.append(page.get_text("text"))
        doc.close()
        full_text = "\n\n".join(pages_text).strip()
        if not full_text:
            return "", "No readable text found in the PDF. It may be a scanned image-only PDF."
        return full_text, ""
    except Exception as e:
        return "", f"Failed to read PDF: {str(e)}"


# ── Image OCR extraction ────────────────────────────────────────────────────

def extract_text_from_image(file_bytes: bytes) -> Tuple[str, str]:
    """
    Extract text from an image using Tesseract OCR.
    Returns (extracted_text, error_message).
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return "", "pytesseract or Pillow is not installed. Run: pip install pytesseract Pillow"

    try:
        image = Image.open(io.BytesIO(file_bytes))
        # Improve OCR accuracy: convert to RGB if needed
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        text = pytesseract.image_to_string(image)
        text = text.strip()
        if not text:
            return "", "No text could be extracted from the image. Ensure the image is clear and contains readable text."
        return text, ""
    except pytesseract.TesseractNotFoundError:
        return "", (
            "Tesseract is not installed or not found in PATH.\n"
            "  macOS: brew install tesseract\n"
            "  Ubuntu: sudo apt install tesseract-ocr\n"
            "  Windows: https://github.com/UB-Mannheim/tesseract/wiki"
        )
    except Exception as e:
        return "", f"Image OCR failed: {str(e)}"
