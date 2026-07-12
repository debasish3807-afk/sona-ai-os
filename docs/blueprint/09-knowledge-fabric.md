# 09 — Knowledge Fabric

> The Knowledge Fabric provides Sona AI OS with retrieval-augmented generation (RAG), graph-based knowledge retrieval, hybrid search, and citation-grounded responses. It ensures the system's outputs are grounded in verifiable, ranked, and validated knowledge.

---

## Overview

The Knowledge Fabric answers: *"What information does the AI need, and how confident are we in it?"*

| Property | Description |
|----------|-------------|
| **Multi-modal retrieval** | Vector, keyword, and graph-based search unified |
| **Quality-scored** | Every piece of retrieved knowledge carries a confidence score |
| **Cited** | All generated content links back to source material |
| **Validated** | Automatic fact-checking and staleness detection |
| **Adaptive** | Weights and strategies adjust based on query type |

---

## RAG Pipeline

The core retrieval-augmented generation flow:

```text
Query → Embed → Retrieve → Rank → Augment → Generate → Cite
```

### Stage Details

| Stage | Input | Output | Description |
|-------|-------|--------|-------------|
| **Query** | User intent + context | Structured query | Parse intent, extract entities, expand query |
| **Embed** | Structured query | Query vector(s) | Generate embeddings for similarity search |
| **Retrieve** | Query vector + filters | Candidate documents | Multi-source parallel retrieval |
| **Rank** | Candidates | Ranked results | Score by relevance, recency, authority |
| **Augment** | Ranked results + query | Enriched context | Assemble context window with citations |
| **Generate** | Enriched context | Draft response | LLM generates grounded response |
| **Cite** | Draft + sources | Final response | Attach citations, confidence scores |

### Query Expansion

Before retrieval, queries are expanded:

- **Synonym expansion**: Add alternative terms
- **Hierarchical expansion**: Include parent/child concepts
- **Contextual expansion**: Add project-specific terminology
- **Temporal expansion**: Consider version-specific knowledge

---

## GraphRAG

Entity-centric retrieval that leverages the Knowledge Graph for richer context.

### Pipeline

```text
1. Entity Extraction — identify entities in the query
2. Graph Traversal — walk relationships from identified entities
3. Context Enrichment — gather connected knowledge subgraph
4. Synthesis — combine graph context with vector results
```

### Traversal Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Breadth-first** | Explore immediate neighbors | General context |
| **Depth-first** | Follow specific relationship chains | Dependency analysis |
| **Weighted** | Prefer high-importance edges | Knowledge prioritization |
| **Filtered** | Only traverse specific edge types | Focused queries |
| **Bounded** | Max depth/width limits | Performance control |

### Entity Extraction

| Method | Description |
|--------|-------------|
| NER (Named Entity Recognition) | Detect people, technologies, files |
| Pattern matching | Detect code identifiers, URLs, paths |
| Context-aware | Resolve ambiguous references from session |
| Knowledge-grounded | Match against known entities in graph |

---

## Hybrid Search

Combines vector, keyword, and graph search with configurable weights.

### Search Modes

| Mode | Vector | Keyword | Graph | Use Case |
|------|--------|---------|-------|----------|
| **Semantic** | 0.7 | 0.2 | 0.1 | Conceptual questions |
| **Exact** | 0.2 | 0.7 | 0.1 | Specific code/API lookup |
| **Exploratory** | 0.3 | 0.2 | 0.5 | Understanding relationships |
| **Balanced** | 0.4 | 0.3 | 0.3 | General purpose |
| **Custom** | user | user | user | User-specified weights |

### Fusion Strategy

```text
1. Execute each search type in parallel
2. Normalize scores to [0, 1] per source
3. Apply mode-specific weights
4. Reciprocal Rank Fusion (RRF) for deduplication
5. Final ranking by fused score
6. Return top-K results with provenance
```

### Adaptive Weight Tuning

Weights are dynamically adjusted based on:
- Query type classification (factual vs. conceptual vs. navigational)
- Historical performance (which mode produced accepted answers)
- Content type (code vs. documentation vs. conversation)

---

## Semantic Search

Embedding-based retrieval for conceptual similarity.

| Component | Description |
|-----------|-------------|
| **Embedding Model** | Configurable (default: sentence-transformers) |
| **Dimensions** | 768–1536 based on model |
| **Index** | HNSW (Hierarchical Navigable Small World) |
| **Distance Metric** | Cosine similarity |
| **Pre-filter** | Metadata filters before vector search |
| **Post-filter** | MMR (Maximal Marginal Relevance) for diversity |

### Cross-Encoder Reranking

After initial retrieval, a cross-encoder reranks results:

```text
1. Retrieve top-100 candidates via bi-encoder
2. Score each (query, candidate) pair with cross-encoder
3. Rerank by cross-encoder score
4. Return top-K reranked results
```

### Chunking Strategy

| Content Type | Chunk Size | Overlap | Strategy |
|--------------|-----------|---------|----------|
| Code | Function/class | 0 | AST-aware boundaries |
| Documentation | Paragraph | 2 sentences | Semantic boundaries |
| Conversation | Turn | 1 turn | Natural boundaries |
| Configuration | Block | 0 | Structural boundaries |

---

## Keyword Search

Traditional information retrieval for exact matches and known terms.

### BM25

| Parameter | Default | Description |
|-----------|---------|-------------|
| `k1` | 1.2 | Term frequency saturation |
| `b` | 0.75 | Document length normalization |
| `fields` | content, title, tags | Searchable fields |
| `boost` | title: 2.0, tags: 1.5 | Field-specific boosting |

### FTS5 (Full-Text Search)

- SQLite FTS5 for local/embedded deployments
- Supports prefix queries, phrase matching, boolean operators
- Trigram index for fuzzy matching and typo tolerance

### Trigram Search

- Character-level n-gram indexing
- Effective for code identifiers and partial matches
- Configurable similarity threshold (default: 0.3)

---

## Citation Engine

Every generated statement is linked to its source material.

### Citation Structure

| Field | Type | Description |
|-------|------|-------------|
| `citation_id` | `UUID` | Unique reference |
| `source_type` | `SourceType` | code, documentation, conversation, knowledge_base |
| `source_ref` | `str` | File path, URL, or memory ID |
| `location` | `Location` | Line numbers, paragraph, section |
| `snippet` | `str` | Relevant excerpt |
| `confidence` | `float` | How well the source supports the claim (0.0–1.0) |
| `retrieved_at` | `datetime` | When the source was accessed |

### Source Tracking

```text
1. During generation, track which context segments are used
2. Map generated tokens back to source segments (attention attribution)
3. Assign confidence based on:
   - Semantic similarity between claim and source
   - Source authority and recency
   - Number of corroborating sources
4. Embed citations inline and as structured metadata
```

### Attribution Policy

| Confidence | Label | Action |
|------------|-------|--------|
| > 0.9 | Verified | Direct citation |
| 0.7 – 0.9 | Supported | Citation with qualifier |
| 0.5 – 0.7 | Inferred | Flag as inference |
| < 0.5 | Uncertain | Explicit uncertainty marker |

---

## Knowledge Ranking

Multi-factor ranking of retrieved knowledge.

### Ranking Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| **Relevance** | 0.35 | Semantic similarity to query |
| **Recency** | 0.25 | How recently the knowledge was created/updated |
| **Authority** | 0.20 | Source reliability (official docs > blog posts) |
| **Diversity** | 0.10 | Penalize redundant results |
| **Specificity** | 0.10 | Prefer precise matches over general ones |

### Authority Scoring

| Source | Authority Score |
|--------|----------------|
| Official documentation | 1.0 |
| Project source code | 0.9 |
| Verified knowledge base | 0.8 |
| Team conventions | 0.7 |
| Community best practices | 0.6 |
| AI-generated summaries | 0.5 |
| Unverified external content | 0.3 |

### Diversity Enforcement

- MMR (Maximal Marginal Relevance) with lambda = 0.7
- Ensure results cover multiple aspects of the query
- Limit results from any single source to 30%

---

## Knowledge Validation

Ensuring retrieved knowledge is accurate, consistent, and current.

### Fact-Checking

| Check | Method | Description |
|-------|--------|-------------|
| **Internal Consistency** | Cross-reference | Does this fact contradict other known facts? |
| **Source Verification** | Provenance check | Is the source still accessible and unchanged? |
| **Temporal Validity** | Staleness check | Is this knowledge still current? |
| **Code Verification** | AST/runtime check | Does cited code still exist and compile? |

### Consistency Detection

```text
1. Extract claims from retrieved knowledge
2. Compare against known facts in Knowledge Graph
3. Flag contradictions with both sources
4. Present conflicts to reasoning engine for resolution
5. Update knowledge base with resolution
```

### Staleness Detection

| Content Type | Staleness Threshold | Revalidation |
|--------------|--------------------|--------------| 
| Code snippets | File modification time | On next access |
| API documentation | 30 days | Periodic crawl |
| Package versions | 7 days | Registry check |
| Team conventions | 90 days | User confirmation |
| General knowledge | 180 days | Confidence decay |

### Validation Pipeline

```text
1. Retrieve candidate knowledge
2. Check last-validated timestamp
3. If stale: trigger revalidation
   a. Verify source still exists
   b. Check for updates at source
   c. Cross-reference with other knowledge
   d. Update confidence score
4. If invalid: mark as deprecated, find replacement
5. Return validated knowledge with freshness metadata
```

---

## Design Principles

- **Retrieval before generation** — never generate from parametric knowledge alone when retrieval is available.
- **Confidence transparency** — always communicate uncertainty to downstream consumers.
- **Source diversity** — avoid single-source dependency for critical facts.
- **Graceful degradation** — if retrieval fails, clearly indicate reduced confidence.
- **Incremental indexing** — re-index only changed content, not the entire corpus.

---

*Next: [10 — Execution Fabric](./10-execution-fabric.md)*
