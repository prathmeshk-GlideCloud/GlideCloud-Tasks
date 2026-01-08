# app/services/chunking_service.py

from typing import List, Dict, Any
from uuid import uuid4
import re


def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs using blank lines.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs


def split_into_sentences(text: str) -> List[str]:
    """
    Simple sentence splitter using punctuation.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def semantic_chunk_text(
    text: str,
    max_words: int = 50,
    overlap_words: int = 10
) -> List[str]:
    """
    Semantic-first chunking:
    - Paragraph based
    - Sentence fallback
    - Word-count bounded
    """

    if not text or not text.strip():
        return []

    paragraphs = split_into_paragraphs(text)
    chunks: List[str] = []

    for para in paragraphs:
        words = para.split()

        # Paragraph already fits
        if len(words) <= max_words:
            chunks.append(para)
            continue

        # Paragraph too large → sentence split
        sentences = split_into_sentences(para)
        current_chunk: List[str] = []

        for sentence in sentences:
            sentence_words = sentence.split()

            if len(current_chunk) + len(sentence_words) <= max_words:
                current_chunk.extend(sentence_words)
            else:
                chunks.append(" ".join(current_chunk))

                # overlap handling
                if overlap_words > 0:
                    current_chunk = current_chunk[-overlap_words:] + sentence_words
                else:
                    current_chunk = sentence_words

        if current_chunk:
            chunks.append(" ".join(current_chunk))

    return chunks


def prepare_chunks(
    *,
    text: str,
    metadata: Dict[str, Any] | None = None,
    max_words: int = 50,
    overlap_words: int = 10,
    doc_id: str | None = None
) -> List[Dict[str, Any]]:
    """
    Prepare semantic chunks with metadata for vector storage.
    """

    metadata = metadata or {}
    doc_id = doc_id or str(uuid4())

    chunks = semantic_chunk_text(
        text=text,
        max_words=max_words,
        overlap_words=overlap_words
    )

    prepared_chunks = []

    for idx, chunk in enumerate(chunks):
        prepared_chunks.append({
            "id": f"{doc_id}_chunk_{idx}",
            "text": chunk,
            "metadata": {
                **metadata,
                "doc_id": doc_id,
                "chunk_index": idx
            }
        })

    return prepared_chunks
