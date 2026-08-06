import re
from dataclasses import dataclass

_CHUNK_SIZE = 600  # 字元數，中英文皆適用的粗略切分單位
_CHUNK_OVERLAP = 100
_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)")


@dataclass
class Chunk:
    index: int
    text: str
    heading: str | None


def chunk_markdown(content_md: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[Chunk]:
    """把 markdown 內容切成有重疊的片段，每段記錄離它最近的上層標題，
    方便之後引用時附上上下文。長文章不會整篇塞進 prompt，只有選中的
    片段才會被使用。"""
    text = content_md.strip()
    if not text:
        return []

    # 記錄每個字元位置對應的「最近標題」
    headings: list[tuple[int, str]] = []
    pos = 0
    for line in content_md.splitlines(keepends=True):
        m = _HEADING_RE.match(line.strip())
        if m:
            headings.append((pos, m.group(1).strip()))
        pos += len(line)

    def heading_at(offset: int) -> str | None:
        current: str | None = None
        for h_offset, h_text in headings:
            if h_offset <= offset:
                current = h_text
            else:
                break
        return current

    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # 盡量在段落或空白邊界切，避免把字切一半（best-effort，非硬性要求）
            boundary = text.rfind("\n\n", start, end)
            if boundary <= start:
                boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(Chunk(index=index, text=chunk_text, heading=heading_at(start)))
            index += 1

        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks
