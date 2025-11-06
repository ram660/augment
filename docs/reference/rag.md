# Agentic RAG Reference

This document describes the data model, services, and APIs for the Retrieval-Augmented Generation (RAG) workflow in this repo, plus performance and quality options you can toggle on as you scale.

## Overview

RAG enables agents to retrieve grounded context from your domain data. The pipeline:

1. Normalize and persist domain rows (homes, rooms, images, analyses) into the DB.
2. Build KnowledgeDocuments from domain entities (room summaries, image analyses, floor plan analyses, room analyses, materials/fixtures/products) with provenance and scoping (home_id, room_id, floor_plan_id, metadata.floor_level).
3. Chunk docs and store Embeddings for each chunk.
4. Query the index with filters (home/room/floor) to retrieve top-k context for agents; optionally hybridize keyword + vector search and re-rank.

## Data Model (files)

- `backend/models/knowledge.py`
  - FileAsset: track files/URLs and basic metadata.
  - KnowledgeDocument: one “unit” of knowledge with provenance (source_type/source_id) and optional scoping (home/room/floor plan).
  - KnowledgeChunk: chunked text per document.
  - Embedding: embedding for a chunk (JSON float array; pgvector later).
  - AgentTask / AgentTrace: agent execution and tool-call trails.
  - RetrievalLog: optional logging of retrieval outcomes.

## Services

- `backend/services/rag_service.py`
  - `build_index(db, home_id=None)`: creates documents from Room, ImageAnalysis, FloorPlanAnalysis, RoomAnalysis, and per-item Material/Fixture/Product summaries; chunks and embeds. `KnowledgeDocument.metadata.floor_level` is set for room docs.
  - `query(db, query, home_id=None, room_id=None, floor_level=None, k=8)`: returns top‑k matches with provenance.
    - Postgres + pgvector: runs in‑DB cosine search on embeddings; supports filter by `home_id`, `room_id`, and `metadata.floor_level`.
    - Fallback (SQLite or no pgvector): computes cosine in Python and post‑filters by `floor_level`.
    - Planned: Hybrid retrieval (keyword BM25/FTS merged with vector via RRF) and optional re‑ranking.

Embeddings

- Default: lightweight, deterministic hashing embedding (portable; zero deps)
- Optional: Sentence-Transformers MiniLM via `EMBEDDING_MODEL=all-minilm-l6-v2` (CPU-friendly, better quality)
- You can substitute OpenAI/Gemini embeddings by swapping the `_embed` implementation.

## API Endpoints

Base path: `/api/digital-twin`

- POST `/rag/reindex`
  - Request: `{ "home_id?": "..." }`
  - Response: `{ "status": "ok", "documents": N, "chunks": M }`

- POST `/rag/query`
  - Request: `{ "query": "...", "home_id?": "...", "room_id?": "...", "floor_level?": 2, "top_k?": 8 }`
  - Response: `{ "matches": [ { "score": 0.87, "chunk_id": "...", "text": "...", "document_id": "...", "title": "...", "source_type": "room|image_analysis|floor_plan", "source_id": "...", "room_id?": "...", "floor_plan_id?": "...", "home_id?": "..." } ] }`

## CSV → DB Import

Use `scripts/import_enriched_csv_to_db.py` to load enriched CSVs into the DB, preserving IDs where present. Rows without essential foreign keys (e.g., `room_images.room_id`) are skipped to maintain referential integrity.

```powershell
python -m scripts.import_enriched_csv_to_db --owner-email demo@example.com
```

## Postgres + pgvector

- When `USE_SQLITE=false`, the app uses Postgres; `init_db_async` enables the `vector` extension and creates an ANN index:
  - `CREATE INDEX IF NOT EXISTS ix_embeddings_vector ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100)`
- The `Embedding.vector` column uses pgvector when available; else it falls back to JSON float arrays.
- The query path uses in‑DB cosine distance ordering (`<=>`) when pgvector is available; otherwise it falls back to Python.

## Filters and Provenance

- `KnowledgeDocument` carries `home_id`, `room_id`, `floor_plan_id` and `metadata.floor_level` (for rooms)
- `query()` supports:
  - `home_id` → scope to a single home
  - `room_id` → scope to a room
  - `floor_level` → filter documents whose `metadata.floor_level` equals the given value (in‑DB filter on Postgres; post‑filter in Python fallback)

## Hybrid Retrieval (recommended)

To improve recall for short labels and domain terms:

- Add keyword search (Postgres FTS or SQLite FTS5) in parallel to vector search
- Merge lists with Reciprocal Rank Fusion (RRF): `score = Σ 1/(k0 + rank)` (k0≈60)
- Optionally re‑rank the top 20–50 with a local cross‑encoder (e.g., `ms-marco-MiniLM-L-6-v2`)

In this repo:

- Postgres: create a functional GIN index to speed queries
  - `CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_text_fts ON knowledge_chunks USING GIN (to_tsvector('english', text))`
- Fallback (SQLite dev): use FTS5 virtual table (future work) or the vector‑only path

## Optional Enhancements

- HyDE: For under‑specified queries, generate a hypothetical answer (once), embed it, and re‑query (cache results)
- Multi‑Modal: Add CLIP image embeddings for `RoomImage` to support text→image and image→image retrieval; fuse with text hits via RRF
- Retrieval logging: fill `RetrievalLog` for evaluation and analytics

## Example (PowerShell)

```powershell
# Rebuild the index
curl.exe -X POST http://localhost:8000/api/digital-twin/rag/reindex -H "Content-Type: application/json" -d "{}"

# Ask a scoped question (floor-level filter)
curl.exe -X POST http://localhost:8000/api/digital-twin/rag/query -H "Content-Type: application/json" -d "{\"query\":\"recommend countertop styles\",\"home_id\":\"<HOME_UUID>\",\"floor_level\":2}"
```
