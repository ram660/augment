"""RAG service: builds knowledge documents/chunks and performs retrieval.

Production-ready implementation with:
- Gemini Text Embedding 004 for semantic search
- Hybrid retrieval (vector + keyword search)
- Context assembly for chat agents
- Caching for performance
"""

from __future__ import annotations
import re
import math
import json
from typing import Any, Dict, Iterable, List, Optional, Tuple
import os
import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, literal, cast, Integer, func, desc

from backend.models import (
    Home, Room, RoomImage, FloorPlan,
    Material, Fixture, Product,
    FloorPlanAnalysis, ImageAnalysis,
    KnowledgeDocument, KnowledgeChunk, Embedding,
)
from backend.models.base import USE_SQLITE
from backend.models.knowledge import PgVector
from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    return str(value)


def _simple_chunk(text: str, max_chars: int = 800) -> List[str]:
    # Very simple character-based chunking at sentence boundaries when possible
    sentences = re.split(r"(?<=[.!?])\s+", text.strip()) if text else []
    chunks: List[str] = []
    buf = ""
    for s in sentences:
        if len(buf) + len(s) + 1 <= max_chars:
            buf = (buf + " " + s).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = s
    if buf:
        chunks.append(buf)
    # fallback if empty
    if not chunks and text:
        for i in range(0, len(text), max_chars):
            chunks.append(text[i:i+max_chars])
    return chunks


def _hash_embedding(text: str, dim: int = 256) -> List[float]:
    """Deterministic hashing-based embedding for portability.

    Not semantically rich, but useful as a placeholder. Returns a list of floats.
    """
    vec = [0.0] * dim
    if not text:
        return vec
    for tok in re.findall(r"\w+", text.lower()):
        h = hash(tok) % dim
        vec[h] += 1.0
    # L2 normalize
    norm = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: List[float], b: List[float]) -> float:
    return sum(x*y for x, y in zip(a, b))


class RAGService:
    """
    Production-ready RAG service with Gemini embeddings and hybrid retrieval.

    Features:
    - Gemini Text Embedding 004 (768 dimensions)
    - Hybrid retrieval (vector + keyword search with RRF)
    - Context assembly for chat agents
    - Query result caching
    - Comprehensive error handling
    """

    model_name: str = "text-embedding-004"

    def __init__(self, use_gemini: bool = True) -> None:
        """
        Initialize RAG service.

        Args:
            use_gemini: Whether to use Gemini embeddings (default: True)
        """
        self._embedder = None
        self._gemini_client = None
        self.dim = 768  # Gemini text-embedding-004 dimension
        self.use_gemini = use_gemini

        # Query cache (simple in-memory cache)
        self._query_cache: Dict[str, Tuple[datetime, Dict[str, Any]]] = {}
        self._cache_ttl_seconds = 300  # 5 minutes

        # Initialize embedding model
        model = os.getenv("EMBEDDING_MODEL", "gemini" if use_gemini else "hash").strip().lower()

        if model == "gemini" and use_gemini:
            try:
                self._gemini_client = GeminiClient()
                self.dim = 768
                self.model_name = "text-embedding-004"
                logger.info("RAG Service initialized with Gemini Text Embedding 004")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}. Falling back to hash embeddings.")
                self._gemini_client = None
                self.dim = 256
                self.model_name = "stub-embedding-v1"

        elif model in ("sbert", "sentence-transformers", "mini-lm", "all-minilm-l6-v2"):
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
                self.dim = 384
                self.model_name = "all-MiniLM-L6-v2"
                logger.info("RAG Service initialized with SentenceTransformers")
            except Exception as e:
                logger.warning(f"Failed to initialize SentenceTransformers: {e}. Falling back to hash embeddings.")
                self._embedder = None
                self.dim = 256
                self.model_name = "stub-embedding-v1"
        else:
            self._embedder = None
            self.dim = 256
            self.model_name = "stub-embedding-v1"
            logger.info("RAG Service initialized with hash embeddings (fallback)")

    async def _embed(self, text: str) -> List[float]:
        """
        Generate embedding for text using configured model.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not text or not text.strip():
            return [0.0] * self.dim

        # Try Gemini first
        if self._gemini_client is not None:
            try:
                embeddings = await self._gemini_client.get_embeddings(text)
                if embeddings and len(embeddings) > 0:
                    return embeddings[0]
            except Exception as e:
                logger.error(f"Gemini embedding failed: {e}. Falling back to hash.")

        # Try SentenceTransformers
        if self._embedder is not None:
            try:
                vec = self._embedder.encode(text, normalize_embeddings=True)
                return [float(x) for x in (vec.tolist() if hasattr(vec, "tolist") else list(vec))]
            except Exception as e:
                logger.error(f"SentenceTransformers embedding failed: {e}. Falling back to hash.")

        # Fallback to hash
        return _hash_embedding(text, dim=self.dim)

    async def build_index(self, db: AsyncSession, home_id: Optional[str] = None) -> Dict[str, Any]:
        """Create KnowledgeDocuments/Chunks/Embeddings from DB rows.

        - Room summaries (include materials/fixtures/products counts)
        - ImageAnalyses
        - FloorPlanAnalyses
        """
        created_docs = 0
        created_chunks = 0

        # Rooms
        q_rooms = select(Room)
        if home_id:
            q_rooms = q_rooms.where(Room.home_id == home_id)
        rooms = (await db.execute(q_rooms)).scalars().all()
        rooms_by_id = {r.id: r for r in rooms}

        # Preload related counts for summary text
        room_ids = [r.id for r in rooms]
        mats_map: Dict[str, int] = {}
        fix_map: Dict[str, int] = {}
        prod_map: Dict[str, int] = {}
        if room_ids:
            mats = (await db.execute(select(Material).where(Material.room_id.in_(room_ids)))).scalars().all()
            fixes = (await db.execute(select(Fixture).where(Fixture.room_id.in_(room_ids)))).scalars().all()
            prods = (await db.execute(select(Product).where(Product.room_id.in_(room_ids)))).scalars().all()
            for m in mats:
                mats_map[str(m.room_id)] = mats_map.get(str(m.room_id), 0) + 1
            for f in fixes:
                fix_map[str(f.room_id)] = fix_map.get(str(f.room_id), 0) + 1
            for p in prods:
                prod_map[str(p.room_id)] = prod_map.get(str(p.room_id), 0) + 1

        for r in rooms:
            title = f"Room: {r.name} ({r.room_type}) - Floor {r.floor_level}"
            summary = (
                f"Type: {r.room_type}. Dimensions: {r.length}x{r.width}x{r.height} ft; Area: {r.area} sq ft. "
                f"Style: {r.style}. Condition score: {r.condition_score}. "
                f"Materials: {mats_map.get(str(r.id), 0)}, Fixtures: {fix_map.get(str(r.id), 0)}, Products: {prod_map.get(str(r.id), 0)}."
            )
            doc = KnowledgeDocument(
                home_id=r.home_id,
                room_id=r.id,
                source_type="room",
                source_id=str(r.id),
                title=title,
                text={"format": "plain", "content": summary},
                meta={"floor_level": r.floor_level},
            )
            db.add(doc)
            await db.flush()
            for idx, ch in enumerate(_simple_chunk(summary)):
                kc = KnowledgeChunk(document_id=doc.id, chunk_index=idx, text=ch, meta={})
                db.add(kc)
                await db.flush()
                emb = Embedding(chunk_id=kc.id, model=self.model_name, vector=await self._embed(ch), dim=self.dim)
                db.add(emb)
                created_chunks += 1
            created_docs += 1

        # Image analyses
        q_img = select(ImageAnalysis)
        if room_ids:
            q_img = q_img.where(ImageAnalysis.room_image_id.isnot(None))
        images = (await db.execute(q_img)).scalars().all()
        for ia in images:
            content = " ".join([
                _to_text(ia.description),
                _to_text(ia.keywords),
                _to_text(ia.objects_detected),
                _to_text(ia.materials_visible),
                _to_text(ia.fixtures_visible),
            ])
            doc = KnowledgeDocument(
                home_id=None,
                room_id=None,  # resolved below if possible
                source_type="image_analysis",
                source_id=str(ia.id),
                title="Image Analysis",
                text={"format": "plain", "content": content},
                meta={},
            )
            # Try to infer room via join through RoomImage
            ri = (await db.execute(select(RoomImage).where(RoomImage.id == ia.room_image_id))).scalar_one_or_none()
            if ri is not None:
                doc.room_id = ri.room_id
                if ri.room_id in rooms_by_id:
                    doc.home_id = rooms_by_id[ri.room_id].home_id
            db.add(doc)
            await db.flush()
            for idx, ch in enumerate(_simple_chunk(content)):
                kc = KnowledgeChunk(document_id=doc.id, chunk_index=idx, text=ch, meta={})
                db.add(kc)
                await db.flush()
                emb = Embedding(chunk_id=kc.id, model=self.model_name, vector=await self._embed(ch), dim=self.dim)
                db.add(emb)
                created_chunks += 1
            created_docs += 1

        # Floor plan analyses
        fpas = (await db.execute(select(FloorPlanAnalysis))).scalars().all()
        for fpa in fpas:
            content = " ".join([
                _to_text(fpa.layout_type),
                _to_text(fpa.features),
                _to_text(fpa.detected_rooms),
                _to_text(fpa.scale_info),
            ])
            doc = KnowledgeDocument(
                home_id=None,
                floor_plan_id=fpa.floor_plan_id,
                source_type="floor_plan",
                source_id=str(fpa.id),
                title="Floor Plan Analysis",
                text={"format": "plain", "content": content},
                meta={},
            )
            # backfill home_id from floor plan
            fp = (await db.execute(select(FloorPlan).where(FloorPlan.id == fpa.floor_plan_id))).scalar_one_or_none()
            if fp is not None:
                doc.home_id = fp.home_id
            db.add(doc)
            await db.flush()
            for idx, ch in enumerate(_simple_chunk(content)):
                kc = KnowledgeChunk(document_id=doc.id, chunk_index=idx, text=ch, meta={})
                db.add(kc)
                await db.flush()
                emb = Embedding(chunk_id=kc.id, model=self.model_name, vector=await self._embed(ch), dim=self.dim)
                db.add(emb)
                created_chunks += 1
            created_docs += 1

        # Room analyses
        from backend.models.analysis import RoomAnalysis
        ras = (await db.execute(select(RoomAnalysis))).scalars().all()
        for ra in ras:
            content = " ".join([
                _to_text(ra.room_type_detected),
                _to_text(ra.style),
                _to_text(ra.color_palette),
                _to_text(ra.materials_detected),
                _to_text(ra.fixtures_detected),
                _to_text(ra.products_detected),
                _to_text(ra.improvement_suggestions),
                _to_text(ra.condition_notes),
            ])
            doc = KnowledgeDocument(
                home_id=None,
                room_id=ra.room_id,
                source_type="room_analysis",
                source_id=str(ra.id),
                title="Room Analysis",
                text={"format": "plain", "content": content},
                meta={},
            )
            db.add(doc)
            await db.flush()
            for idx, ch in enumerate(_simple_chunk(content)):
                kc = KnowledgeChunk(document_id=doc.id, chunk_index=idx, text=ch, metadata={})
                db.add(kc)
                await db.flush()
                emb = Embedding(chunk_id=kc.id, model=self.model_name, vector=await self._embed(ch), dim=self.dim)
                db.add(emb)
                created_chunks += 1
            created_docs += 1

        # Materials / Fixtures / Products summaries
        if room_ids:
            # Materials
            mats = (await db.execute(select(Material).where(Material.room_id.in_(room_ids)))).scalars().all()
            for m in mats:
                text = f"Material {m.material_type} category {m.category} color {m.color} finish {m.finish} condition {m.condition}"
                doc = KnowledgeDocument(
                    home_id=None,
                    room_id=m.room_id,
                    source_type="material",
                    source_id=str(m.id),
                    title=f"Material: {m.material_type}",
                    text={"format": "plain", "content": text},
                    metadata={},
                )
                if m.room_id in rooms_by_id:
                    doc.home_id = rooms_by_id[m.room_id].home_id
                db.add(doc)
                await db.flush()
                for idx, ch in enumerate(_simple_chunk(text)):
                    kc = KnowledgeChunk(document_id=doc.id, chunk_index=idx, text=ch, meta={})
                    db.add(kc)
                    await db.flush()
                    db.add(Embedding(chunk_id=kc.id, model=self.model_name, vector=await self._embed(ch), dim=self.dim))
                    created_chunks += 1
                created_docs += 1

            # Fixtures
            fixes = (await db.execute(select(Fixture).where(Fixture.room_id.in_(room_ids)))).scalars().all()
            for f in fixes:
                text = f"Fixture {f.fixture_type} style {f.style} finish {f.finish} location {f.location} condition {f.condition}"
                doc = KnowledgeDocument(
                    home_id=None,
                    room_id=f.room_id,
                    source_type="fixture",
                    source_id=str(f.id),
                    title=f"Fixture: {f.fixture_type}",
                    text={"format": "plain", "content": text},
                    meta={},
                )
                if f.room_id in rooms_by_id:
                    doc.home_id = rooms_by_id[f.room_id].home_id
                db.add(doc)
                await db.flush()
                for idx, ch in enumerate(_simple_chunk(text)):
                    kc = KnowledgeChunk(document_id=doc.id, chunk_index=idx, text=ch, meta={})
                    db.add(kc)
                    await db.flush()
                    db.add(Embedding(chunk_id=kc.id, model=self.model_name, vector=await self._embed(ch), dim=self.dim))
                    created_chunks += 1
                created_docs += 1

            # Products
            prods = (await db.execute(select(Product).where(Product.room_id.in_(room_ids)))).scalars().all()
            for p in prods:
                text = f"Product {p.product_type} category {p.product_category} brand {p.brand} color {p.color} material {p.material} condition {p.condition}"
                doc = KnowledgeDocument(
                    home_id=None,
                    room_id=p.room_id,
                    source_type="product",
                    source_id=str(p.id),
                    title=f"Product: {p.product_type}",
                    text={"format": "plain", "content": text},
                    meta={},
                )
                if p.room_id in rooms_by_id:
                    doc.home_id = rooms_by_id[p.room_id].home_id
                db.add(doc)
                await db.flush()
                for idx, ch in enumerate(_simple_chunk(text)):
                    kc = KnowledgeChunk(document_id=doc.id, chunk_index=idx, text=ch, meta={})
                    db.add(kc)
                    await db.flush()
                    db.add(Embedding(chunk_id=kc.id, model=self.model_name, vector=await self._embed(ch), dim=self.dim))
                    created_chunks += 1
                created_docs += 1

        await db.commit()
        return {"documents": created_docs, "chunks": created_chunks}

    async def query(self, db: AsyncSession, query: str, home_id: Optional[str] = None, room_id: Optional[str] = None, floor_level: Optional[int] = None, k: int = 8) -> Dict[str, Any]:
        """Simple cosine similarity over stored embeddings with filters."""
        q_emb = select(Embedding).join(KnowledgeChunk).join(KnowledgeDocument)
        if home_id:
            q_emb = q_emb.where(KnowledgeDocument.home_id == home_id)
        if room_id:
            q_emb = q_emb.where(KnowledgeDocument.room_id == room_id)
        # floor_level lives in metadata of document
        results = (await db.execute(q_emb)).scalars().all()
        if not results:
            return {"matches": []}

        # If pgvector is available and DB is Postgres, do in-DB cosine distance ordering
        if not USE_SQLITE and PgVector is not None:
            q_vec = await self._embed(query)
            qv = cast(literal(q_vec), PgVector(self.dim))
            # Build the statement with cosine distance (smaller is closer). Convert to similarity as 1 - distance.
            dist = Embedding.vector.op('<=>')(qv)
            # Vector path (retrieve more for fusion)
            kv = max(k * 3, 8)
            stmt = (
                select(
                    (1 - dist).label('score'),
                    KnowledgeChunk.id.label('chunk_id'),
                    KnowledgeChunk.text.label('text'),
                    KnowledgeDocument.id.label('document_id'),
                    KnowledgeDocument.title.label('title'),
                    KnowledgeDocument.source_type.label('source_type'),
                    KnowledgeDocument.source_id.label('source_id'),
                    KnowledgeDocument.room_id.label('room_id'),
                    KnowledgeDocument.floor_plan_id.label('floor_plan_id'),
                    KnowledgeDocument.home_id.label('home_id'),
                )
                .select_from(Embedding)
                .join(KnowledgeChunk, KnowledgeChunk.id == Embedding.chunk_id)
                .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
            )
            if home_id:
                stmt = stmt.where(KnowledgeDocument.home_id == home_id)
            if room_id:
                stmt = stmt.where(KnowledgeDocument.room_id == room_id)
            if floor_level is not None:
                # Filter by JSON metadata floor_level for Postgres
                stmt = stmt.where(
                    cast(KnowledgeDocument.meta['floor_level'].astext, Integer) == floor_level
                )
            stmt = stmt.order_by(dist.asc()).limit(kv)
            rows_vec = (await db.execute(stmt)).all()

            # Keyword path (Postgres full-text search) for hybrid retrieval
            rows_kw = []
            try:
                if query and query.strip():
                    ts_query = func.plainto_tsquery('english', literal(query))
                    ts_vector = func.to_tsvector('english', KnowledgeChunk.text)
                    kw_rank = func.ts_rank(ts_vector, ts_query).label('kw_score')
                    stmt_kw = (
                        select(
                            kw_rank,
                            KnowledgeChunk.id.label('chunk_id'),
                            KnowledgeChunk.text.label('text'),
                            KnowledgeDocument.id.label('document_id'),
                            KnowledgeDocument.title.label('title'),
                            KnowledgeDocument.source_type.label('source_type'),
                            KnowledgeDocument.source_id.label('source_id'),
                            KnowledgeDocument.room_id.label('room_id'),
                            KnowledgeDocument.floor_plan_id.label('floor_plan_id'),
                            KnowledgeDocument.home_id.label('home_id'),
                        )
                        .select_from(KnowledgeChunk)
                        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
                        .where(ts_vector.op('@@')(ts_query))
                    )
                    if home_id:
                        stmt_kw = stmt_kw.where(KnowledgeDocument.home_id == home_id)
                    if room_id:
                        stmt_kw = stmt_kw.where(KnowledgeDocument.room_id == room_id)
                    if floor_level is not None:
                        stmt_kw = stmt_kw.where(
                            cast(KnowledgeDocument.meta['floor_level'].astext, Integer) == floor_level
                        )
                    stmt_kw = stmt_kw.order_by(desc('kw_score')).limit(kv)
                    rows_kw = (await db.execute(stmt_kw)).all()
            except Exception:
                # If FTS isn't available, skip keyword path
                rows_kw = []

            # If keyword path empty, return vector results directly
            if not rows_kw:
                return {"matches": [
                    {
                        "score": float(r.score),
                        "chunk_id": str(r.chunk_id),
                        "text": r.text,
                        "document_id": str(r.document_id),
                        "title": r.title,
                        "source_type": r.source_type,
                        "source_id": r.source_id,
                        "room_id": str(r.room_id) if r.room_id else None,
                        "floor_plan_id": str(r.floor_plan_id) if r.floor_plan_id else None,
                        "home_id": str(r.home_id) if r.home_id else None,
                    }
                for r in rows_vec[:k]]}

            # Reciprocal Rank Fusion (RRF)
            def rrf_ranks(rows, key_fn):
                return {key_fn(r): i+1 for i, r in enumerate(rows)}

            key = lambda r: str(r.chunk_id)
            ranks_vec = rrf_ranks(rows_vec, key)
            ranks_kw = rrf_ranks(rows_kw, key)
            k0 = 60.0
            fused: dict[str, dict] = {}

            # Stash row accessors
            def row_to_obj(r, score_field: Optional[str] = None):
                base = {
                    "chunk_id": str(r.chunk_id),
                    "text": r.text,
                    "document_id": str(r.document_id),
                    "title": r.title,
                    "source_type": r.source_type,
                    "source_id": r.source_id,
                    "room_id": str(r.room_id) if r.room_id else None,
                    "floor_plan_id": str(r.floor_plan_id) if r.floor_plan_id else None,
                    "home_id": str(r.home_id) if r.home_id else None,
                }
                if score_field == 'vec':
                    base["vec_score"] = float(r.score)
                if score_field == 'kw':
                    try:
                        base["kw_score"] = float(r.kw_score)
                    except Exception:
                        pass
                return base

            for r in rows_vec:
                cid = key(r)
                fused[cid] = row_to_obj(r, 'vec')
            for r in rows_kw:
                cid = key(r)
                if cid not in fused:
                    fused[cid] = row_to_obj(r, 'kw')

            # Compute fused score
            out = []
            for cid, obj in fused.items():
                rv = ranks_vec.get(cid)
                rk = ranks_kw.get(cid)
                s = 0.0
                if rv is not None:
                    s += 1.0 / (k0 + rv)
                if rk is not None:
                    s += 1.0 / (k0 + rk)
                obj["score"] = s
                out.append(obj)

            out.sort(key=lambda x: x["score"], reverse=True)
            return {"matches": out[:k]}

        # Fallback: in-Python cosine
        q_vec = await self._embed(query)
        scored: List[Tuple[float, Embedding]] = []
        for emb in results:
            score = _cosine(q_vec, emb.vector or [])
            scored.append((score, emb))
        scored.sort(key=lambda x: x[0], reverse=True)
        # We'll scan in order and post-filter by floor_level (if provided)
        payload = []
        for score, emb in scored:
            kc = (await db.execute(select(KnowledgeChunk).where(KnowledgeChunk.id == emb.chunk_id))).scalar_one_or_none()
            if not kc:
                continue
            doc = (await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == kc.document_id))).scalar_one_or_none()
            if not doc:
                continue
            if floor_level is not None:
                try:
                    doc_floor = None
                    if isinstance(doc.meta, dict):
                        doc_floor = doc.meta.get("floor_level")
                    # Accept ints as strings too
                    if doc_floor is not None and int(doc_floor) != int(floor_level):
                        continue
                except Exception:
                    # If metadata missing or unparsable, skip when filtering by floor
                    continue
            payload.append({
                "score": float(score),
                "chunk_id": str(kc.id),
                "text": kc.text,
                "document_id": str(doc.id),
                "title": doc.title,
                "source_type": doc.source_type,
                "source_id": doc.source_id,
                "room_id": str(doc.room_id) if doc.room_id else None,
                "floor_plan_id": str(doc.floor_plan_id) if doc.floor_plan_id else None,
                "home_id": str(doc.home_id) if doc.home_id else None,
            })
            if len(payload) >= k:
                break

        return {"matches": payload}

    async def assemble_context(
        self,
        db: AsyncSession,
        query: str,
        home_id: Optional[str] = None,
        room_id: Optional[str] = None,
        floor_level: Optional[int] = None,
        k: int = 8,
        include_images: bool = True
    ) -> Dict[str, Any]:
        """
        Assemble comprehensive context for chat agents.

        Args:
            db: Database session
            query: User query
            home_id: Filter by home ID
            room_id: Filter by room ID
            floor_level: Filter by floor level
            k: Number of chunks to retrieve
            include_images: Whether to include image URLs in context

        Returns:
            Assembled context with text chunks, metadata, and optional images
        """
        # Check cache first
        cache_key = f"{query}:{home_id}:{room_id}:{floor_level}:{k}"
        if cache_key in self._query_cache:
            cached_time, cached_result = self._query_cache[cache_key]
            if (datetime.utcnow() - cached_time).total_seconds() < self._cache_ttl_seconds:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_result

        # Retrieve relevant chunks
        retrieval_result = await self.query(
            db=db,
            query=query,
            home_id=home_id,
            room_id=room_id,
            floor_level=floor_level,
            k=k
        )

        matches = retrieval_result.get("matches", [])

        if not matches:
            return {
                "context_text": "",
                "chunks": [],
                "metadata": {
                    "total_chunks": 0,
                    "sources": [],
                    "has_images": False
                }
            }

        # Assemble context text
        context_chunks = []
        sources = set()
        image_urls = []

        for match in matches:
            chunk_text = match.get("text", "")
            source_type = match.get("source_type", "unknown")
            score = match.get("score", 0.0)

            context_chunks.append({
                "text": chunk_text,
                "source": source_type,
                "score": score,
                "document_id": match.get("document_id"),
                "chunk_id": match.get("chunk_id")
            })

            sources.add(source_type)

        # Optionally fetch related images
        if include_images and home_id:
            try:
                # Get room images for this home
                room_images_query = select(RoomImage).join(Room).where(Room.home_id == home_id)
                if room_id:
                    room_images_query = room_images_query.where(RoomImage.room_id == room_id)

                room_images = (await db.execute(room_images_query.limit(5))).scalars().all()
                image_urls = [img.image_url for img in room_images if img.image_url]

                # Get floor plan images
                floor_plans = (await db.execute(
                    select(FloorPlan).where(FloorPlan.home_id == home_id).limit(2)
                )).scalars().all()
                image_urls.extend([fp.image_url for fp in floor_plans if fp.image_url])

            except Exception as e:
                logger.warning(f"Failed to fetch images: {e}")

        # Build context text
        context_text = "\n\n".join([
            f"[{chunk['source']}] {chunk['text']}"
            for chunk in context_chunks
        ])

        result = {
            "context_text": context_text,
            "chunks": context_chunks,
            "metadata": {
                "total_chunks": len(context_chunks),
                "sources": list(sources),
                "has_images": len(image_urls) > 0,
                "image_count": len(image_urls),
                "query": query
            },
            "images": image_urls if include_images else []
        }

        # Cache the result
        self._query_cache[cache_key] = (datetime.utcnow(), result)

        # Clean old cache entries (simple LRU)
        if len(self._query_cache) > 100:
            oldest_key = min(self._query_cache.keys(), key=lambda k: self._query_cache[k][0])
            del self._query_cache[oldest_key]

        return result

    def clear_cache(self):
        """Clear the query cache."""
        self._query_cache.clear()
        logger.info("RAG query cache cleared")
