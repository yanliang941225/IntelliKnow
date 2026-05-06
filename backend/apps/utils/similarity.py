"""Similarity detection module using SimHash."""
import hashlib
import re
from typing import List, Tuple, Optional
import logging

import jieba
import numpy as np

logger = logging.getLogger(__name__)


class SimHash:
    """SimHash implementation for text similarity detection."""

    def __init__(self, hash_size: int = 64):
        self.hash_size = hash_size

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize Chinese and English text."""
        text = self._clean_text(text)
        words = jieba.lcut(text)
        return [w for w in words if len(w) > 1]

    def _clean_text(self, text: str) -> str:
        """Clean text by removing special characters."""
        if not text:
            return ""
        text = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', text)
        return ' '.join(text.split())

    def _hash(self, token: str) -> int:
        """Generate hash for a token."""
        if isinstance(token, str):
            token = token.encode('utf-8')
        digest = hashlib.md5(token).hexdigest()
        return int(digest, 16)

    def compute(self, text: str) -> str:
        """Compute SimHash fingerprint for text."""
        tokens = self._tokenize(text)
        if not tokens:
            return "0" * self.hash_size

        v = np.zeros(self.hash_size, dtype=int)

        for token in tokens:
            hash_val = self._hash(token)
            for i in range(self.hash_size):
                bit = (hash_val >> i) & 1
                v[i] += 1 if bit else -1

        fingerprint = 0
        for i in range(self.hash_size):
            if v[i] > 0:
                fingerprint |= (1 << i)

        return format(fingerprint, '064b')

    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate Hamming distance between two hashes."""
        h1 = int(hash1, 2)
        h2 = int(hash2, 2)
        xor = h1 ^ h2
        return bin(xor).count('1')

    def similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two hashes (0-1)."""
        distance = self.hamming_distance(hash1, hash2)
        return 1 - (distance / self.hash_size)


class ContentDeduplicator:
    """Content deduplication service."""

    def __init__(self, threshold: float = 0.85):
        self.simhash = SimHash()
        self.threshold = threshold

    def generate_fingerprint(self, content: str) -> str:
        """Generate fingerprint for content."""
        return self.simhash.compute(content)

    def is_duplicate(
        self,
        new_content: str,
        existing_fingerprints: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """Check if content is duplicate against existing fingerprints.

        Returns:
            Tuple of (is_duplicate, matched_fingerprint)
        """
        if not existing_fingerprints:
            return False, None

        new_fingerprint = self.generate_fingerprint(new_content)

        for fp in existing_fingerprints:
            similarity = self.simhash.similarity(new_fingerprint, fp)
            if similarity >= self.threshold:
                return True, fp

        return False, None

    def find_similar(
        self,
        content: str,
        existing_fingerprints: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find similar content from existing fingerprints.

        Returns:
            List of (fingerprint, similarity) tuples sorted by similarity.
        """
        if not existing_fingerprints:
            return []

        new_fingerprint = self.generate_fingerprint(content)
        similarities = []

        for fp in existing_fingerprints:
            sim = self.simhash.similarity(new_fingerprint, fp)
            if sim > 0:
                similarities.append((fp, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class TFIDFSimilarity:
    """TF-IDF based similarity detection for longer texts."""

    def __init__(self):
        self.corpus: List[str] = []
        self.vectors: Optional[np.ndarray] = None

    def fit(self, documents: List[str]):
        """Build TF-IDF model from documents."""
        import math
        from collections import Counter

        self.corpus = [self._tokenize(d) for d in documents]

        df = Counter()
        for doc in self.corpus:
            for word in set(doc):
                df[word] += 1

        n = len(self.corpus)
        idf = {word: math.log(n / (df[word] + 1)) + 1 for word in df}

        self.vectors = np.zeros((n, len(idf)))
        word_to_idx = {w: i for i, w in enumerate(idf.keys())}

        for i, doc in enumerate(self.corpus):
            tf = Counter(doc)
            for word, freq in tf.items():
                if word in word_to_idx:
                    tfidf = freq * idf[word]
                    self.vectors[i, word_to_idx[word]] = tfidf

        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        self.vectors = self.vectors / norms

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text."""
        import re
        text = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', text)
        return [w for w in jieba.lcut(text) if len(w) > 1]

    def cosine_similarity(self, text: str) -> np.ndarray:
        """Calculate cosine similarity between text and all documents."""
        import math
        from collections import Counter

        if self.vectors is None or len(self.corpus) == 0:
            return np.array([])

        doc_tokens = self._tokenize(text)
        tf = Counter(doc_tokens)
        idf = {}

        df = Counter()
        for doc in self.corpus:
            for word in set(doc):
                df[word] += 1

        n = len(self.corpus)
        idf = {word: math.log(n / (df[word] + 1)) + 1 for word in df}

        word_to_idx = {w: i for i, w in enumerate(idf.keys())}

        vec = np.zeros(len(idf))
        for word, freq in tf.items():
            if word in word_to_idx:
                vec[word_to_idx[word]] = freq * idf[word]

        norm = np.linalg.norm(vec)
        if norm == 0:
            return np.zeros(len(self.corpus))

        vec = vec / norm
        similarities = np.dot(self.vectors, vec)

        return similarities


deduplicator = ContentDeduplicator(threshold=0.85)
