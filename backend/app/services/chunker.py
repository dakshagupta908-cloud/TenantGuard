import io
import re
from typing import Dict, List
from pypdf import PdfReader


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages_text: List[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        if extracted.strip():
            pages_text.append(extracted.strip())
    return "\n\n".join(pages_text)


def chunk_statutory_text(raw_text: str, max_chars: int = 900) -> List[Dict[str, str]]:
    """
    Splits raw statutory text into logical section chunks.
    Detects section headers like '§ 27-2029', 'Section 44', or falls back to paragraph chunking.
    """
    cleaned = re.sub(r"\r\n", "\n", raw_text).strip()
    if not cleaned:
        return []

    section_pattern = re.compile(
        r"(?m)^((?:§+\s*[\w\-\.]+|Section\s+[\w\-\.]+|RPL\s*§\s*[\w\-\.]+))\s*[:\-–]?\s*(.*)$"
    )
    matches = list(section_pattern.finditer(cleaned))

    chunks: List[Dict[str, str]] = []
    if matches:
        for idx, match in enumerate(matches):
            sec_code = match.group(1).strip()
            heading = match.group(2).strip() or "Statutory Provision"
            start_pos = match.end()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(cleaned)
            body = cleaned[start_pos:end_pos].strip()
            if not body:
                body = heading
            chunks.append(
                {
                    "section_code": sec_code[:120],
                    "heading": heading[:250],
                    "content": body[:max_chars],
                }
            )
        return chunks

    # Fallback: split by double newline into numbered clauses
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if len(p.strip()) >= 20]
    for i, para in enumerate(paragraphs, start=1):
        first_line = para.split("\n")[0][:80]
        chunks.append(
            {
                "section_code": f"Clause {i}",
                "heading": first_line,
                "content": para[:max_chars],
            }
        )
    return chunks
