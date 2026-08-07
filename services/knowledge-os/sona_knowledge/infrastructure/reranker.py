"""Re-ranking module for Knowledge OS.

Re-scores results after initial retrieval to improve quality
through cross-encoder simulation, relevance boosting, and diversity.
"""

import re
from collections import Counter

import structlog

from sona_knowledge.infrastructure.hybrid_search import HybridResult

logger = structlog.get_logger()


class Reranker:
    """Re-ranks search results for improved quality.

    Applies:
    - Cross-encoder simulation (boost exact query matches)
    - Relevance re-scoring based on query-chunk term overlap
    - Diversity penalty (reduce redundant chunks from same document)
    """

    def __init__(
        self,
        exact_match_boost: float = 0.2,
        diversity_penalty: float = 0.1,
    ) -> None:
        """Initialize the reranker.

        Args:
            exact_match_boost: Score boost for exact query phrase matches.
            diversity_penalty: Penalty for chunks from the same document.
        """
        self._exact_match_boost = exact_match_boost
        self._diversity_penalty = diversity_penalty

    def rerank(self, query: str, results: list[HybridResult]) -> list[HybridResult]:
        """Re-rank results with improved scoring.

        Args:
            query: The original search query.
            results: Initial search results to re-rank.

        Returns:
            Re-ranked list of HybridResult with updated combined_score.
        """
        if not results:
            return []

        query_terms = self._tokenize(query)
        seen_documents: Counter[str] = Counter()

        reranked: list[HybridResult] = []

        for result in results:
            # Start with original combined score
            score = result.combined_score

            # Cross-encoder simulation: boost exact phrase matches
            score += self._exact_match_score(query, result.content)

            # Term overlap relevance
            score += self._term_overlap_score(query_terms, result.content)

            # Diversity penalty for same-document chunks
            doc_id = str(result.metadata.get("document_id", ""))
            if doc_id and seen_documents[doc_id] > 0:
                score -= self._diversity_penalty * seen_documents[doc_id]
            seen_documents[doc_id] += 1

            reranked.append(
                HybridResult(
                    id=result.id,
                    content=result.content,
                    semantic_score=result.semantic_score,
                    keyword_score=result.keyword_score,
                    combined_score=max(0.0, score),
                    metadata=result.metadata,
                )
            )

        reranked.sort(key=lambda r: r.combined_score, reverse=True)

        logger.debug(
            "reranking_complete",
            query=query[:50],
            results_count=len(reranked),
        )
        return reranked

    def _exact_match_score(self, query: str, content: str) -> float:
        """Score boost for exact query phrase appearing in content."""
        if query.lower() in content.lower():
            return self._exact_match_boost
        # Check for significant sub-phrases (3+ words)
        words = query.split()
        if len(words) >= 3:
            for i in range(len(words) - 2):
                phrase = " ".join(words[i : i + 3])
                if phrase.lower() in content.lower():
                    return self._exact_match_boost * 0.5
        return 0.0

    def _term_overlap_score(self, query_terms: list[str], content: str) -> float:
        """Score based on fraction of query terms found in content."""
        if not query_terms:
            return 0.0
        content_lower = content.lower()
        matches = sum(1 for term in query_terms if term in content_lower)
        overlap_ratio = matches / len(query_terms)
        # Scale to modest boost range [0, 0.1]
        return overlap_ratio * 0.1

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase terms."""
        return [w.lower() for w in re.findall(r"\w+", text)]
