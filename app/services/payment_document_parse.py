"""Bounded document import; uploaded content is data, never executable code."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import httpx

from app.services.payment_image_parse import extract_payment_text_from_image, parse_payment_image
from app.services.payment_text_parse import parse_payment_text

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024


async def parse_payment_document(data: bytes, filename: str, content_type: str | None):
    if not data or len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("Choose a non-empty document up to 10 MB")
    suffix = Path(filename).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
        return await parse_payment_image(image_bytes=data, content_type=types[suffix])
    if suffix == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF document")
        if b"/Encrypt" in data:
            raise ValueError("Password-protected PDFs must be unlocked before upload")
        try:
            text = await extract_payment_text_from_image(image_bytes=data, media_type="application/pdf")
        except httpx.HTTPError as exc:
            raise RuntimeError("PDF recognition failed. Check the document; password-protected PDFs must be unlocked before upload.") from exc
    elif suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                info = archive.getinfo("word/document.xml")
                if info.file_size > 2 * 1024 * 1024:
                    raise ValueError("Word document text exceeds the import limit")
                xml = archive.read(info)
                if b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
                    raise ValueError("Unsupported XML declarations")
                root = ElementTree.fromstring(xml)
                ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                text = "\n".join("".join(p.itertext()) for p in root.iter(ns + "p"))
        except (zipfile.BadZipFile, KeyError, ElementTree.ParseError, RuntimeError) as exc:
            raise ValueError("Cannot read Word document. Export legacy or protected Word files to an unlocked PDF or DOCX.") from exc
    elif suffix in {".txt", ".csv", ".md", ".json", ".xml"}:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Text documents must use UTF-8 encoding") from exc
    else:
        raise ValueError("Unsupported format. Upload PDF, DOCX, TXT, CSV, MD, JSON, XML, JPEG, PNG, WebP or GIF.")
    if not text.strip():
        raise ValueError("No readable text found. For scanned Word files, upload a PDF or photo instead.")
    if len(text) > 32000:
        raise ValueError("Document text is too long; upload only the payment pages (up to 32,000 characters)")
    parsed = parse_payment_text(text, source="ocr")
    parsed.parse_notes.insert(0, "Imported payment document; verify extracted fields against the original")
    return parsed
