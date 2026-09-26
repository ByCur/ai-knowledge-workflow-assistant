from pathlib import Path

from pypdf import PdfReader


def extract_text_from_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages)


def extract_text_from_txt(file_path: Path) -> str:
    return file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )


def extract_text(
    file_path: Path,
    content_type: str
) -> str:
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_path)

    if content_type == "text/plain":
        return extract_text_from_txt(file_path)

    raise ValueError(
        f"Unsupported file type: {content_type}"
    )