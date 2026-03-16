from __future__ import annotations

import requests

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sentence_transformers import SentenceTransformer


QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "md_chunks_demo"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OLLAMA_URL = "http://192.168.1.109:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"
LIMIT = 5
QUERY_FILTER = Filter(
    must_not=[
        FieldCondition(key="is_noise", match=MatchValue(value=True)),
    ]
)


def build_context(results) -> str:
    parts: list[str] = []
    for index, point in enumerate(results.points, start=1):
        payload = point.payload or {}
        source = payload.get("source", "")
        section_title = payload.get("section_title", "")
        text = payload.get("text", "")
        parts.append(
            f"[Chunk {index}]\n"
            f"Source: {source}\n"
            f"Section: {section_title}\n"
            f"Content:\n{text}"
        )
    return "\n\n".join(parts)


def build_prompt(question: str, context: str) -> str:
    return (
        "You are a helpful assistant.\n"
        "Answer the user's question only from the provided context.\n"
        "If the answer is not in the context, say you do not know.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{question}\n\n"
        "Answer:"
    )


def query_qdrant(question: str, client: QdrantClient, model: SentenceTransformer):
    query_vector = model.encode(question).tolist()
    return client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=LIMIT,
        with_payload=True,
        query_filter=QUERY_FILTER,
    )


def ask_ollama(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


def print_sources(results) -> None:
    print("Retrieved chunks:")
    for index, point in enumerate(results.points, start=1):
        payload = point.payload or {}
        source = payload.get("source", "")
        section_title = payload.get("section_title", "")
        doc_group = payload.get("doc_group", "")
        print(f"[{index}] score={point.score:.4f} | {doc_group} | {source} | {section_title}")
    print()


def main() -> None:
    client = QdrantClient(url=QDRANT_URL)
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Qdrant: {QDRANT_URL} / collection={COLLECTION_NAME}")
    print(f"Ollama: {OLLAMA_URL} / model={OLLAMA_MODEL}")
    print("Type a question. Type 'exit' or 'quit' to stop.")

    while True:
        try:
            question = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue

        if question.lower() in {"exit", "quit"}:
            break

        results = query_qdrant(question, client, model)
        context = build_context(results)
        prompt = build_prompt(question, context)

        print()
        print_sources(results)

        try:
            answer = ask_ollama(prompt)
        except Exception as error:
            print(f"Ollama request failed: {error}")
            print()
            continue

        print("Answer:")
        print(answer)
        print()


if __name__ == "__main__":
    main()
