import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

COLLECTION_NAME = "amaru_policies"
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db"))

SIMILARITY_THRESHOLD = 0.3


def get_vectorstore() -> Chroma:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_PERSIST_DIR),
    )


def query_knowledge_base(query: str, top_k: int = 5) -> dict:
    vectorstore = get_vectorstore()

    results_with_scores = vectorstore.similarity_search_with_score(query, k=top_k)

    parsed_results = []
    for doc, score in results_with_scores:
        distance_score = 1.0 - score
        parsed_results.append(
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "desconocido"),
                "metadata": {k: v for k, v in doc.metadata.items() if k != "source"},
                "score": round(distance_score, 4),
            }
        )

    found = any(r["score"] >= SIMILARITY_THRESHOLD for r in parsed_results)

    return {"results": parsed_results, "found": found}


def test_query(query: str = "¿Cuántos días de vacaciones tengo?") -> None:
    result = query_knowledge_base(query)
    print(f"Query: {query}")
    print(f"Found: {result['found']}")
    for r in result["results"]:
        print(f"  [{r['score']:.4f}] {r['source']} — {r['content'][:80]}...")
