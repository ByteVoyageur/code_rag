from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sentence_transformers import SentenceTransformer


QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "md_chunks_demo"
MODEL_NAME = "all-MiniLM-L6-v2"
LIMIT = 5
QUERY_FILTER = Filter(
    must_not=[
        FieldCondition(key="is_noise", match=MatchValue(value=True)),
    ]
)


def print_results(question: str, client: QdrantClient, model: SentenceTransformer) -> None:
    query_vector = model.encode(question).tolist()
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=LIMIT,
        with_payload=True,
        query_filter=QUERY_FILTER,
    )

    print()
    print(f"Question: {question}")
    print(f"Top {LIMIT} chunks:")
    print()

    for index, point in enumerate(results.points, start=1):
        payload = point.payload or {}
        source = payload.get("source", "")
        section_title = payload.get("section_title", "")
        doc_group = payload.get("doc_group", "")
        text = payload.get("text", "")
        preview = text[:500].replace("\n", " ")

        print(f"[{index}] score={point.score:.4f}")
        print(f"source: {source}")
        print(f"group: {doc_group}")
        print(f"section: {section_title}")
        print(f"text: {preview}")
        print()


def main() -> None:
    client = QdrantClient(url=QDRANT_URL)
    model = SentenceTransformer(MODEL_NAME)

    print(f"Connected to {COLLECTION_NAME} at {QDRANT_URL}")
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

        print_results(question, client, model)


if __name__ == "__main__":
    main()
