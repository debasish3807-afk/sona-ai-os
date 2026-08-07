"""Hybrid search combining semantic and keyword-based retrieval.

Merges vector similarity (semantic) with BM25-style term frequency
(keyword) scoring using weighted fusion.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass

import structlog

from sona_knowledge.infrastructure.vector_store import SearchResult

logger = structlog.get_logger()


@dataclass
class HybridResult:
    """Result from hybrid search with combined scoring."""

    id: str
    content: str
    semantic_score: float
    keyword_score: float
    combined_score: float
    metadata: dict[str, object]


class HybridSearch:
    """Combines semantic similarity with keyword matching.

    Uses weighted fusion of:
    - Vector similarity (cosine) for semantic understanding
    - BM25-style term frequency for exact keyword matching
    """

    def __init__(
        self,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> None:
        """Initialize hybrid search.

        Args:
            semantic_weight: Weight for semantic similarity scores.
            keyword_weight: Weight for keyword matching scores.
        """
        self._semantic_weight = semantic_weight
        self._keyword_weight = keyword_weight

    def search(
        self,
        query: str,
        semantic_results: list[SearchResult],
        corpus_size: int = 100,
    ) -> list[HybridResult]:
        """Perform hybrid search combining semantic and keyword signals.

        Args:
            query: The search query text.
            semantic_results: Results from vector similarity search.
            corpus_size: Estimated total corpus size for IDF calculation.

        Returns:
            List of HybridResult sorted by combined score.
        """
        query_terms = self._tokenize(query)

        results: list[HybridResult] = []

        for result in semantic_results:
            keyword_score = self._bm25_score(
                query_terms=query_terms,
                document=result.content,
                avg_doc_length=200.0,
                corpus_size=corpus_size,
                doc_freq=self._estimate_doc_freq(query_terms, semantic_results),
            )
            # Normalize keyword score to [0, 1] range
            normalized_keyword = min(1.0, keyword_score / 5.0) if keyword_score > 0 else 0.0

            combined = (
                self._semantic_weight * result.score + self._keyword_weight * normalized_keyword
            )

            results.append(
                HybridResult(
                    id=result.id,
                    content=result.content,
                    semantic_score=result.score,
                    keyword_score=normalized_keyword,
                    combined_score=combined,
                    metadata=result.metadata,
                )
            )

        results.sort(key=lambda r: r.combined_score, reverse=True)

        logger.debug(
            "hybrid_search_complete",
            query=query[:50],
            results_count=len(results),
        )
        return results

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase terms."""
        return [w.lower() for w in re.findall(r"\w+", text)]

    def _bm25_score(
        self,
        query_terms: list[str],
        document: str,
        avg_doc_length: float,
        corpus_size: int,
        doc_freq: dict[str, int],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> float:
        """Compute BM25-style relevance score.

        Args:
            query_terms: Tokenized query terms.
            document: Document text content.
            avg_doc_length: Average document length in corpus.
            corpus_size: Total number of documents in corpus.
            doc_freq: Document frequency for each query term.
            k1: Term frequency saturation parameter.
            b: Length normalization parameter.

        Returns:
            BM25 relevance score.
        """
        doc_terms = self._tokenize(document)
        doc_length = len(doc_terms)
        term_counts = Counter(doc_terms)
        score = 0.0

        for term in query_terms:
            tf = term_counts.get(term, 0)
            df = doc_freq.get(term, 1)
            # IDF component
            idf = math.log((corpus_size - df + 0.5) / (df + 0.5) + 1.0)
            # TF component with length normalization
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * doc_length / avg_doc_length)
            score += idf * (numerator / denominator) if denominator > 0 else 0.0

        return score

    def _estimate_doc_freq(
        self, query_terms: list[str], results: list[SearchResult]
    ) -> dict[str, int]:
        """Estimate document frequency from the result set."""
        doc_freq: dict[str, int] = {}
        for term in query_terms:
            count = sum(1 for r in results if term.lower() in r.content.lower())
            doc_freq[term] = max(1, count)
        return doc_freq
