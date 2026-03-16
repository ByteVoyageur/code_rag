"""Markdown chunking utilities and CLI export script."""

from __future__ import annotations

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "data" / "kdk" / "docs"
OUTPUT_PATH = ROOT_DIR / "outputs" / "md_chunks.jsonl"


def extract_doc_title(lines: list[str], fallback: str) -> str:
    """Extract the first H1 title from a markdown file."""
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip()
    return fallback


def split_oversized_chunk(
    text: str,
    metadata: dict,
    max_chars: int,
) -> list[dict]:
    """Split an oversized chunk on paragraph and line boundaries."""
    stripped = text.strip()
    if not stripped or len(stripped) <= max_chars:
        return [{"text": stripped, "metadata": metadata}]

    pieces: list[dict] = []
    paragraphs = [part.strip() for part in stripped.split("\n\n") if part.strip()]
    current = ""
    part_idx = 1

    def flush() -> None:
        nonlocal current, part_idx
        if not current.strip():
            return
        part_metadata = dict(metadata)
        if part_idx > 1:
            part_metadata["section_title"] = f"{metadata['section_title']} (part {part_idx})"
        pieces.append({"text": current.strip(), "metadata": part_metadata})
        current = ""
        part_idx += 1

    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        flush()

        if len(paragraph) <= max_chars:
            current = paragraph
            continue

        lines = [line for line in paragraph.splitlines() if line.strip()]
        current_line_block = ""
        for line in lines:
            candidate_line = line if not current_line_block else f"{current_line_block}\n{line}"
            if len(candidate_line) <= max_chars:
                current_line_block = candidate_line
                continue

            if current_line_block:
                current = current_line_block
                flush()
                current_line_block = ""

            start = 0
            while start < len(line):
                segment = line[start:start + max_chars]
                current = segment
                flush()
                start += max_chars

        if current_line_block:
            current = current_line_block
            flush()

    flush()
    return pieces


def chunk_markdown_file(filepath: Path, docs_dir: Path, max_chars: int | None = None) -> list[dict]:
    """Chunk a single markdown file by H2 sections, with optional max-length fallback splitting."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()
    rel_path = str(filepath.relative_to(docs_dir))
    doc_title = extract_doc_title(lines, filepath.stem)

    chunks: list[dict] = []
    current_title = doc_title
    current_lines: list[str] = []

    def append_chunk(section_title: str, raw_lines: list[str]) -> None:
        if not raw_lines:
            return
        chunk = {
            "text": "\n".join(raw_lines).strip(),
            "metadata": {
                "source": rel_path,
                "doc_title": doc_title,
                "section_title": section_title,
            },
        }
        if max_chars is None:
            chunks.append(chunk)
        else:
            chunks.extend(split_oversized_chunk(chunk["text"], chunk["metadata"], max_chars))

    for line in lines:
        if line.startswith("## "):
            append_chunk(current_title, current_lines)
            current_title = line[3:].strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    append_chunk(current_title, current_lines)
    return chunks


def chunk_markdown_corpus(docs_dir: Path, max_chars: int | None = None) -> list[dict]:
    """Chunk all markdown files in a directory tree."""
    all_chunks: list[dict] = []
    for filepath in sorted(docs_dir.rglob("*.md")):
        all_chunks.extend(chunk_markdown_file(filepath, docs_dir, max_chars=max_chars))
    return all_chunks


def save_chunks_jsonl(chunks: list[dict], output_path: Path) -> None:
    """Atomically replace the output file to avoid partial writes on failure."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8") as out:
            for chunk in chunks:
                out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        temp_path.replace(output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def step6_process_all_and_save(
    docs_dir: Path = DOCS_DIR,
    output_path: Path = OUTPUT_PATH,
    max_chars: int | None = None,
) -> list[dict]:
    """Process the markdown corpus and save chunks to JSONL."""
    chunks = chunk_markdown_corpus(docs_dir, max_chars=max_chars)
    save_chunks_jsonl(chunks, output_path)
    print(f"Processed {len(list(docs_dir.rglob('*.md')))} markdown files")
    print(f"Wrote {len(chunks)} chunks")
    print(f"Output file: {output_path}")
    return chunks


if __name__ == "__main__":
    step6_process_all_and_save()
