import re
from dataclasses import dataclass
from functools import lru_cache

TARGET_TOKENS = 500
MAX_TOKENS = 800
OVERLAP_TOKENS = 60

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    seq: int
    text: str
    token_count: int


@lru_cache(maxsize=1)
def _encoding():
    import tiktoken

    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_encoding().encode(text))


def _split_oversize(paragraph: str) -> list[str]:
    """Split a paragraph that exceeds MAX_TOKENS on sentence boundaries."""
    sentences = _SENTENCE_RE.split(paragraph)
    parts: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if current and count_tokens(candidate) > MAX_TOKENS:
            parts.append(current)
            current = sentence
        else:
            current = candidate
        # a single sentence longer than MAX_TOKENS: hard-split on tokens
        while count_tokens(current) > MAX_TOKENS:
            tokens = _encoding().encode(current)
            parts.append(_encoding().decode(tokens[:MAX_TOKENS]))
            current = _encoding().decode(tokens[MAX_TOKENS:])
    if current:
        parts.append(current)
    return parts


def _overlap_tail(text: str) -> str:
    tokens = _encoding().encode(text)
    if len(tokens) <= OVERLAP_TOKENS:
        return text
    return _encoding().decode(tokens[-OVERLAP_TOKENS:])


def chunk_text(text: str) -> list[Chunk]:
    """Greedily pack paragraphs into ~TARGET_TOKENS chunks with a small overlap tail."""
    paragraphs: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if count_tokens(para) > MAX_TOKENS:
            paragraphs.extend(_split_oversize(para))
        else:
            paragraphs.append(para)

    chunks: list[Chunk] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if current and count_tokens(candidate) > TARGET_TOKENS:
            chunks.append(Chunk(seq=len(chunks), text=current, token_count=count_tokens(current)))
            current = f"{_overlap_tail(current)}\n\n{para}"
        else:
            current = candidate
    if current:
        chunks.append(Chunk(seq=len(chunks), text=current, token_count=count_tokens(current)))
    return chunks
