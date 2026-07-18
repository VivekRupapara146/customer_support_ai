"""
FAISS-backed vector store.

Single-node, in-process — documented scaling boundary from the M0 decision
doc (fine for a capstone-scale knowledge base, not a "thousands of users"
production deployment without further work).

Vectors and their metadata (source text + source file) are kept in lockstep
by index position, and persisted together so a restart doesn't lose the
mapping from FAISS row -> chunk content.
"""
import json
import pickle
from pathlib import Path

import faiss
import numpy as np

from core.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    def __init__(self, dimension: int):
        self._dimension = dimension
        self._index = faiss.IndexFlatIP(dimension)  # inner product on normalized vectors = cosine similarity
        self._metadata: list[dict] = []

    def add(self, vectors: list[list[float]], metadata: list[dict]) -> None:
        if len(vectors) != len(metadata):
            raise ValueError("vectors and metadata must be the same length")
        if not vectors:
            return

        arr = np.array(vectors, dtype="float32")
        faiss.normalize_L2(arr)
        self._index.add(arr)
        self._metadata.extend(metadata)

    def search(self, query_vector: list[float], top_k: int = 4) -> list[dict]:
        if self._index.ntotal == 0:
            return []

        arr = np.array([query_vector], dtype="float32")
        faiss.normalize_L2(arr)
        scores, indices = self._index.search(arr, min(top_k, self._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append({**self._metadata[idx], "score": float(score)})
        return results

    def save(self, directory: str) -> None:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(path / "index.faiss"))
        with open(path / "metadata.pkl", "wb") as f:
            pickle.dump(self._metadata, f)
        with open(path / "manifest.json", "w") as f:
            json.dump({"dimension": self._dimension, "count": len(self._metadata)}, f)
        logger.info(f"Vector store saved to {directory} ({len(self._metadata)} chunks)")

    @classmethod
    def load(cls, directory: str) -> "VectorStore":
        path = Path(directory)
        with open(path / "manifest.json") as f:
            manifest = json.load(f)

        store = cls(dimension=manifest["dimension"])
        store._index = faiss.read_index(str(path / "index.faiss"))
        with open(path / "metadata.pkl", "rb") as f:
            store._metadata = pickle.load(f)
        logger.info(f"Vector store loaded from {directory} ({len(store._metadata)} chunks)")
        return store
