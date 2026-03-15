from pathlib import Path


def extract_text(file_path: str, content_type: str) -> str | None:
    if not content_type.startswith("text/"):
        return None
    return Path(file_path).read_text(encoding="utf-8")


def split_into_chunks(
    text: str, chunk_size: int = 512, overlap: int = 50
) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap

    return chunks
