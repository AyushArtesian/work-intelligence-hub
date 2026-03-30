from __future__ import annotations

import math
from typing import Any

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover
    faiss = None


class InMemoryVectorStore:
    def __init__(self) -> None:
        self.index = None
        self.dimension: int | None = None
        self.id_map: list[str] = []
        self.doc_to_index: dict[str, int] = {}
        self.vectors: list[list[float]] = []

    def add_embedding(self, doc_id: str, embedding: list[float]) -> None:
        if not embedding:
            return

        if doc_id in self.doc_to_index:
            return

        if self.dimension is None:
            self.dimension = len(embedding)
            self._init_index(self.dimension)

        if len(embedding) != self.dimension:
            raise ValueError(f"Embedding dimension mismatch: expected {self.dimension}, got {len(embedding)}")

        normalized = self._normalize(embedding)

        if faiss is not None and self.index is not None:
            self.index.add(self._to_faiss_matrix([normalized]))

        self.doc_to_index[doc_id] = len(self.id_map)
        self.id_map.append(doc_id)
        self.vectors.append(normalized)

    def search_similar(self, query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        if not query_embedding or not self.id_map:
            return []

        normalized_query = self._normalize(query_embedding)
        k = max(1, min(top_k, len(self.id_map)))

        if faiss is not None and self.index is not None:
            distances, indices = self.index.search(self._to_faiss_matrix([normalized_query]), k)
            results: list[dict[str, Any]] = []
            for score, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self.id_map):
                    continue
                results.append({"doc_id": self.id_map[idx], "score": float(score)})
            return results

        scored = []
        for idx, vec in enumerate(self.vectors):
            score = sum(a * b for a, b in zip(normalized_query, vec))
            scored.append((score, idx))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [{"doc_id": self.id_map[idx], "score": float(score)} for score, idx in scored[:k]]

    def _init_index(self, dim: int) -> None:
        if faiss is None:
            self.index = None
            return
        self.index = faiss.IndexFlatIP(dim)

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]

    @staticmethod
    def _to_faiss_matrix(vectors: list[list[float]]):
        import array

        rows = len(vectors)
        cols = len(vectors[0])
        flat = array.array("f", [0.0] * (rows * cols))
        offset = 0
        for vec in vectors:
            flat[offset : offset + cols] = array.array("f", vec)
            offset += cols

        import numpy as np

        return np.frombuffer(flat, dtype=np.float32).reshape(rows, cols)


_vector_store = InMemoryVectorStore()


def get_vector_store() -> InMemoryVectorStore:
    return _vector_store


def add_embedding(doc_id: str, embedding: list[float]) -> None:
    _vector_store.add_embedding(doc_id, embedding)


def search_similar(query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
    return _vector_store.search_similar(query_embedding, top_k=top_k)
