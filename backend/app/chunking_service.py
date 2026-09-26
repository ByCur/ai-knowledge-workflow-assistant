def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[str]:
    text = text.strip()

    if not text:
        return []

    chunks: list[str] = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(
            start + chunk_size,
            text_length,
        )

        chunk = text[start:end]

        if end < text_length:
            last_break = max(
                chunk.rfind("\n"),
                chunk.rfind(". "),
                chunk.rfind(" "),
            )

            if last_break > chunk_size // 2:
                end = start + last_break + 1
                chunk = text[start:end]

        chunk = chunk.strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = max(
            end - overlap,
            start + 1,
        )

    return chunks