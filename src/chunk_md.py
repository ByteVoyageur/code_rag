"""
Chunker for Markdown files.

Usage:
    python src/chunkers/chunk_md.py
"""

from pathlib import Path
import json

ROOT_DIR = Path(__file__).parent.parent.parent
DOCS_DIR = ROOT_DIR / "data" / "kdk" / "docs"
OUTPUT_DIR = ROOT_DIR / "outputs" / "md_chunks.jsonl"

def read_one_md_file():
    test_file = DOCS_DIR / "about" / "introduction.md"
    text = test_file.read_text(encoding="utf-8")
    print(f"file path: {test_file}")
    print(f"file size: {len(text)} characters")
    print(f"file content 200 lignes: ")
    print(text[:200])

def find_all_md_files():
    list_md_files = []
    md_files = list(DOCS_DIR.rglob("*.md"))
    print(f"Found {len(md_files)} Markdown files in {DOCS_DIR}")
    for md_file in md_files:
        list_md_files.append(md_file)
    print(f"Total Markdown files found: {len(list_md_files)}")    
    print(f"First 5 Markdown files: {list_md_files[:5]}")

def split_md_file_by_two_dieses():
    test_file = DOCS_DIR / "about" / "introduction.md"
    text = test_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    chunks = []
    current_title = None
    current_chunk = []
    
    for line in lines:
        if line.startswith("## "):
            if current_lines:
                chunks.append(
                    {
                        "title": current_title,
                        "content": "\n".join(current_chunk)
                    }

                )
            current_title = line[3:].strip()  # Remove "## " prefix
            current_chunk = []
        else:
            current_chunk.append(line)

    # Append the last chunk if it exists
    if current_chunk:
        chunks.append(
            {
                "title": current_title,
                "content": "\n".join(current_chunk)
            }
            
        )
    print(f"Total chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):
        print(f"Chunk {i+1} (length: {len(chunk['content'])} characters):")
        print(f"Title: {chunk['title']}")
        print(chunk['content'][:200])  # Print first 200 characters of each chunk
        print("\n---\n")

def add_metadata_to_chunks():
    test_file = DOCS_DIR / "about" / "introduction.md"
    text = test_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    doc_title = test_file.stem
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            doc_title = line[2:].strip()
            break

    chunks = []
    current_title = doc_title
    current_chunk = []
    
    for line in lines:
        if line.startswith("## "):
            if current_chunk:
                chunks.append(
                    {
                        "text": "\n".join(current_chunk).strip(),
                        "metadata": {
                            "source": str(test_file.relative_to(DOCs_DIR)),
                            "doc_title": doc_title,
                            "section_title": current_title,
                        }
                    }
                )
            current_title = line[3:].strip()  # Remove "## " prefix
            current_chunk = []
        else:
            current_chunk.append(line)

    # Append the last chunk if it exists
    if current_chunk:
        chunks.append(
            {
                "text": "\n".join(current_chunk).strip(),
                "metadata": {
                    "source": str(test_file.relative_to(DOCS_DIR)),
                    "doc_title": doc_title,
                    "section_title": current_title,
                }
            }
        )
    
    print(f"Total chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):
        print(f"Chunk {i+1} (length: {len(chunk['text'])} characters):")
        print(f"Metadata: {chunk['metadata']}")
        print(chunk['text'][:200])  # Print first 200 characters of each chunk
        print("\n---\n")

def step6_process_all_and_save():
    md_files = sorted(DOCS_DIR.rglob("*.md"))
    OUTPUT_DIR.parent.mkdir(parents=True, exist_ok=True)

    total_chunks = 0
    with OUTPUT_DIR.open("w", encoding="utf-8") as out:
        for filepath in md_files:
            text = filepath.read_text(encoding="utf-8")
            lines = text.splitlines()
            rel_path = filepath.relative_to(DOCS_DIR)

            # find F1 title as doc_title
            doc_title = filepath.stem
            for line in lines:
                if line.startswith("# ") and not line.startswith("## "):
                    doc_title = line[2:].strip()
                    break

            current_title = doc_title
            current_lines = []

            for line in lines:
                if line.startswith("## "):
                    if current_lines:
                        chunk = {
                            "text": "\n".join(current_lines).strip(),
                            "metadata": {
                                "source": str(rel_path),
                                "doc_title": doc_title,
                                "section_title": current_title,
                            },
                        }
                        out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                        total_chunks += 1
                    current_title = line[3:].strip()
                    current_lines = [line]
                else:
                    current_lines.append(line)

            if current_lines:
                chunk = {
                    "text": "\n".join(current_lines).strip(),
                    "metadata": {
                        "source": str(rel_path),
                        "doc_title": doc_title,
                        "section_title": current_title,
                    },
                }
                out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                total_chunks += 1

    print(f"处理了 {len(md_files)} 个文件")
    print(f"写入了 {total_chunks} 个 chunks")
    print(f"输出文件: {OUTPUT_DIR}")

if __name__ == "__main__":
    read_one_md_file()
    find_all_md_files()
    split_md_file_by_two_dieses()
    add_metadata_to_chunks()
    step6_process_all_and_save()
