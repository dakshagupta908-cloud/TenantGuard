# TenantGuard System Architecture & Engineering Trade-Offs

## 1. High-Level Overview
TenantGuard is a full-stack Retrieval-Augmented Generation (RAG) legal research and document automation web application built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL / SQLite**, and **React 18 + TypeScript**.

```text
[React 18 + TypeScript SPA]
         │ (REST / JSON + Bearer JWT)
         ▼
[FastAPI Application Layer] ──► [In-Memory Rate Limiter & JWT / Admin Guards]
         │
         ├──► [RAG Service & Citation-ID Validator]
         │          ├── 1. Jurisdiction Filter (SQL)
         │          ├── 2. In-Process Cosine Ranking over JSON Embeddings
         │          ├── 3. Minimum Similarity Abstention Gate
         │          ├── 4. Grounded Synthesis (Mock / OpenAI-Compatible)
         │          └── 5. Post-Generation Citation ID Filtering & Abstention
         │
         └──► [SQLAlchemy 2.0 Persistence Layer (PostgreSQL 16 / SQLite)]
```

## 2. Citation-ID Validation & Known Limitations
Rather than trusting raw LLM output blindly, `rag_service.py` enforces **post-generation citation-ID filtering**:
1. Every statutory chunk in `legal_chunks` has a primary key `id` and `section_code`.
2. During synthesis, the model is instructed to return `cited_chunk_ids` corresponding to the retrieved candidate chunks.
3. Post-generation, `rag_service.py` intersects `cited_chunk_ids` against the exact dictionary of retrieved chunks (`allowed_by_id`). Any fabricated ID is stripped and incremented in `stripped_hallucinations_count`.
4. **No Blind Fallback:** If the synthesizer returns zero valid retrieved chunk IDs, TenantGuard triggers **Safe Abstention** rather than falling back to displaying unverified text.
5. **Engineering Trade-off (Referential Integrity vs. Semantic Entailment):** Validating `chunk_id` guarantees that every displayed statutory card and section number exists in the indexed corpus, but it does not prove semantic entailment of free-text prose inside `summary_explanation`. Demand letters mitigate this by quoting the exact statutory excerpt text directly from the database record.

## 3. Vector Storage & Scaling Path
- **Current Implementation:** Embeddings are stored in a portable SQL `JSON` column (`LegalChunk.embedding`) and scored in Python after filtering by `jurisdiction`. Because municipal housing code corpora per jurisdiction typically contain a few hundred to a few thousand sections, pre-filtering by indexed `jurisdiction` in SQL and computing cosine similarity in Python executes in milliseconds while allowing zero-dependency `SQLite` execution in local development and CI.
- **Production Scaling Path:** If the corpus grows beyond ~50,000 chunks per jurisdiction, replace the `JSON` column with `pgvector`'s `Vector(dim)` type and an `HNSW` index (`vector_cosine_ops`).
