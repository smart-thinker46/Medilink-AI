from dataclasses import dataclass


@dataclass
class TextChunk:
    index: int
    text: str


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[TextChunk]:
    if not text.strip():
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")
    chunks: list[TextChunk] = []
    start = 0
    index = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        if end < len(text):
            boundary = max(text.rfind("\n\n", start, end), text.rfind(" ", start, end))
            if boundary > start + chunk_size // 2:
                end = boundary
        value = text[start:end].strip()
        if value:
            chunks.append(TextChunk(index, value))
            index += 1
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks
