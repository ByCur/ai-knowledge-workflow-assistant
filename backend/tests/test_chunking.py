from app.chunking_service import chunk_text


def test_empty_text_returns_no_chunks():
    result = chunk_text("")

    assert result == []


def test_short_text_creates_one_chunk():
    text = "prueba para aplicacion"

    result = chunk_text(text)

    assert len(result) == 1
    assert result[0] == text


def test_long_text_creates_multiple_chunks():
    text = "Docker es una plataforma. " * 200

    result = chunk_text(
        text,
        chunk_size=500,
        overlap=50,
    )

    assert len(result) > 1


def test_chunks_are_not_empty():
    text = "Docker " * 500

    result = chunk_text(
        text,
        chunk_size=300,
        overlap=50,
    )

    assert all(
        chunk.strip()
        for chunk in result
    )