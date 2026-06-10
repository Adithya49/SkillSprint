"""Resume and document parsing utilities."""

from __future__ import annotations

from io import BytesIO
from typing import BinaryIO


class PDFParseError(RuntimeError):
    """Raised when a PDF cannot be parsed by available parsers."""


def extract_text_from_pdf(file_obj: BinaryIO | BytesIO) -> str:
    """Extract text from a PDF using pdfplumber first, then PyPDF2."""

    data = file_obj.read()
    if not data:
        return ""

    errors: list[str] = []

    try:
        import pdfplumber

        with pdfplumber.open(BytesIO(data)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        text = "\n".join(page.strip() for page in pages if page.strip())
        if text.strip():
            return text.strip()
    except Exception as exc:  # pragma: no cover - parser-specific failures vary
        errors.append(f"pdfplumber: {exc}")

    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(page.strip() for page in pages if page.strip())
        if text.strip():
            return text.strip()
    except Exception as exc:  # pragma: no cover - parser-specific failures vary
        errors.append(f"PyPDF2: {exc}")

    raise PDFParseError("Unable to extract text from PDF. " + " | ".join(errors))


def extract_text_from_upload(uploaded_file) -> str:
    """Extract text from a Streamlit upload object."""

    if uploaded_file is None:
        return ""

    name = getattr(uploaded_file, "name", "").lower()
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)

    if name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)

    raw = uploaded_file.read()
    if isinstance(raw, str):
        return raw.strip()

    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore").strip()

