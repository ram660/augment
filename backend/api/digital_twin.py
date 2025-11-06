"""Digital Twin API endpoints."""

import logging
from typing import List, Optional
from uuid import UUID
import uuid as uuid_lib
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.models.base import get_async_db
from backend.models import Home, Room, User, UserType, HomeType
from backend.services import DigitalTwinService
from backend.services.rag_service import RAGService
from backend.utils.room_type_normalizer import get_unknown_room_types, add_room_type_synonym
from backend.utils.linking import rank_candidates
# Avoid importing heavy chat stack at module import time; import inside endpoint when needed

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/digital-twin", tags=["Digital Twin"])

# Pydantic models for request/response
class CreateHomeRequest(BaseModel):
    """Request model for creating a home."""
    owner_email: Optional[str] = "user@homevision.ai"  # Default email for now
    name: str
    address: dict
    home_type: str = "single_family"
    year_built: Optional[int] = None
    square_footage: Optional[int] = None
    num_bedrooms: Optional[int] = None
    num_bathrooms: Optional[float] = None
    num_floors: Optional[int] = None


class HomeResponse(BaseModel):
    """Response model for home data."""
    id: str
    name: str
    address: dict
    home_type: str
    digital_twin_completeness: float
    total_rooms: int = 0
    total_images: int = 0

    class Config:
        from_attributes = True


class FloorPlanUploadResponse(BaseModel):
    """Response model for floor plan upload.

    Note: When multi-floor sheets are detected, floor_plan_ids will contain multiple IDs
    and floor_plan_id may be omitted. For single-floor, floor_plan_ids will contain a
    single element and floor_plan_id will mirror that value when available.
    """
    floor_plan_id: Optional[str] = None
    floor_plan_ids: Optional[List[str]] = None
    rooms_created: int
    room_ids: List[str]
    message: str
    multi_floor: Optional[bool] = None
    sheet_id: Optional[str] = None
    # Enriched fields from model analysis (optional)
    floor_level: Optional[int] = None
    floor_level_name: Optional[str] = None
    scale_text: Optional[str] = None


class RoomImageUploadResponse(BaseModel):
    """Response model for room image upload."""
    image_id: str
    materials_created: int
    fixtures_created: int
    products_created: int
    message: str


class DigitalTwinResponse(BaseModel):
    """Response model for complete digital twin data."""
    home_id: str
    address: dict
    home_type: str
    basic_info: dict
    digital_twin_completeness: float
    floor_plans: List[dict]
    rooms: List[dict]
    total_rooms: int
    total_images: int

# Bulk import request/response
class ImportRoomImagesRequest(BaseModel):
    directory: Optional[str] = Field(None, description="Directory to scan; defaults to uploads/room_images")


class ImportRoomImagesResponse(BaseModel):
    directory: str
    total_found: int
    matched: int
    analyzed: int
    skipped: int
    errors: List[str] = []


class IngestFloorplanJsonRequest(BaseModel):
    json_path: str = Field(..., description="Path to floor plan analysis JSON")
    image_url: Optional[str] = Field(None, description="Optional image URL to associate with floor plan rows")
    name_prefix: Optional[str] = Field(None, description="Optional prefix for floor plan names")


class IngestImageLinksAnalysesRequest(BaseModel):
    links_path: str = Field(..., description="Path to links JSON (image_room_links_v2.json)")
    analyses_path: str = Field(..., description="Path to DB-aligned analyses JSON (image_analyses_db_aligned.json)")
    rename_files: bool = Field(False, description="Whether to rename image files to canonical names")
    score_threshold: float = Field(1.5, description="Minimum score to persist a link")


class BulkUploadResult(BaseModel):
    ingested: int
    skipped: int
    errors: List[str] = []
    analyses_saved: int
    links_built: int


# RAG request/response models
class RAGReindexRequest(BaseModel):
    home_id: Optional[str] = None


class RAGQueryRequest(BaseModel):
    query: str
    home_id: Optional[str] = None
    room_id: Optional[str] = None
    floor_level: Optional[int] = None
    top_k: int = 8


# ==============================
# Studio (CSV-backed) endpoints
# ==============================

def _read_csv(path: Path):
    import csv
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _portable_url(url: str) -> str:
    if not url:
        return url
    # Normalize backslashes
    url = str(url).replace("\\", "/")
    # If already relative to uploads, prefix with / so browser can fetch from FastAPI static
    if url.startswith("uploads/"):
        return "/" + url
    # If absolute path contains /uploads/, trim up to uploads
    parts = url.split("/")
    if "uploads" in parts:
        idx = parts.index("uploads")
        return "/" + "/".join(parts[idx:])
    return url


@router.get("/studio/data", response_model=dict)
async def get_studio_data():
    """Assemble a studio-friendly JSON payload from enriched CSV exports.

    Looks under exports/analysis_run/enriched first, then falls back to exports/analysis_run.
    Returns a dict with: home, floor_plans, rooms (with images/materials/fixtures/products),
    room_images map, image_analyses map.
    """
    root = Path(__file__).resolve().parents[2]
    base = root / "exports" / "analysis_run"
    enriched = base / "enriched"
    data_dir = enriched if enriched.exists() else base

    # Load CSVs
    home_rows = _read_csv(data_dir / "home.csv")
    fp_rows = _read_csv(data_dir / "floor_plans.csv")
    fpa_rows = _read_csv(data_dir / "floor_plan_analyses.csv")
    room_rows = _read_csv(data_dir / "rooms.csv")
    ri_rows = _read_csv(data_dir / "room_images.csv")
    ia_rows = _read_csv(data_dir / "image_analyses.csv")
    mat_rows = _read_csv(data_dir / "materials.csv")
    prod_rows = _read_csv(data_dir / "products.csv")
    fix_rows = _read_csv(data_dir / "fixtures.csv")

    # Index helpers
    floor_plans_by_id = {r.get("id"): r for r in fp_rows}
    analyses_by_image = {}
    for a in ia_rows:
        rid = a.get("room_image_id")
        if rid:
            analyses_by_image.setdefault(rid, []).append(a)

    # Build room_images with portable urls
    room_images = {}
    for r in ri_rows:
        img = dict(r)
        img["image_url"] = _portable_url(img.get("image_url"))
        room_images[img.get("id")] = img

    # Map materials/products/fixtures to rooms
    mats_by_room = {}
    for m in mat_rows:
        rid = m.get("room_id")
        if rid:
            mats_by_room.setdefault(rid, []).append(m)
    prods_by_room = {}
    for p in prod_rows:
        rid = p.get("room_id")
        if rid:
            prods_by_room.setdefault(rid, []).append(p)
    fix_by_room = {}
    for f in fix_rows:
        rid = f.get("room_id")
        if rid:
            fix_by_room.setdefault(rid, []).append(f)

    # Rooms with images/materials/fixtures/products
    rooms_full = []
    for r in room_rows:
        rid = r.get("id")
        # Attach images for this room
        images = [ri for ri in ri_rows if (ri.get("room_id") == rid)]
        for im in images:
            im["image_url"] = _portable_url(im.get("image_url"))
        rooms_full.append({
            **r,
            "images": images,
            "materials": mats_by_room.get(rid, []),
            "fixtures": fix_by_room.get(rid, []),
            "products": prods_by_room.get(rid, []),
        })

    # Floor plan analyses keyed to floor_plan_id
    fpa_by_fp = {}
    for a in fpa_rows:
        fid = a.get("floor_plan_id")
        if fid:
            fpa_by_fp.setdefault(fid, []).append(a)

    # Portable URLs for floor plans
    floor_plans = []
    for fp in fp_rows:
        item = dict(fp)
        item["image_url"] = _portable_url(item.get("image_url"))
        item["analyses"] = fpa_by_fp.get(item.get("id"), [])
        floor_plans.append(item)

    # Image analyses map with JSON fields parsed where possible
    import json as _json
    image_analyses = {}
    for a in ia_rows:
        row = dict(a)
        for key in ("keywords", "dominant_colors", "objects_detected", "materials_visible", "fixtures_visible"):
            val = row.get(key)
            if val and isinstance(val, str):
                try:
                    row[key] = _json.loads(val)
                except Exception:
                    # try to split simple comma-separated
                    if "," in val and "[" not in val and "{" not in val:
                        row[key] = [x.strip() for x in val.split(",") if x.strip()]
        image_analyses[row.get("id") or f"img_{row.get('room_image_id')}"] = row

    # Choose home
    home = (home_rows[0] if home_rows else {"id": None, "name": "Studio Home"})

    return {
        "home": home,
        "floor_plans": floor_plans,
        "rooms": rooms_full,
        "room_images": list(room_images.values()),
        "image_analyses": image_analyses,
        "source": str(data_dir)
    }


@router.post("/rag/reindex", response_model=dict)
async def rag_reindex(req: RAGReindexRequest, db: AsyncSession = Depends(get_async_db)):
    """Build knowledge docs/chunks/embeddings from current DB rows.

    This uses a lightweight hashing-based embedding for portability. You can
    later swap to a stronger embedding model without changing the schema.
    """
    try:
        svc = RAGService()
        res = await svc.build_index(db, home_id=req.home_id)
        return {"status": "ok", **res}
    except Exception as e:
        logger.error(f"RAG reindex failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/query", response_model=dict)
async def rag_query(req: RAGQueryRequest, db: AsyncSession = Depends(get_async_db)):
    """Query the RAG index and return top-k matches with provenance."""
    try:
        svc = RAGService()
        res = await svc.query(
            db,
            query=req.query,
            home_id=req.home_id,
            room_id=req.room_id,
            floor_level=req.floor_level,
            k=req.top_k,
        )
        return res
    except Exception as e:
        logger.error(f"RAG query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



# Utility function to save uploaded files
async def save_upload_file(upload_file: UploadFile, destination: Path) -> str:
    """Save uploaded file to destination."""
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        with open(destination, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)
        
        return str(destination)
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


# API Endpoints

@router.get("/homes", response_model=List[HomeResponse])
async def list_homes(
    db: AsyncSession = Depends(get_async_db),
    limit: int = 100
):
    """
    List all homes.

    Returns a list of all homes in the system.
    """
    try:
        from sqlalchemy import select, func
        from sqlalchemy.orm import selectinload

        # Query homes with room counts and images
        result = await db.execute(
            select(Home)
            .options(
                selectinload(Home.rooms).selectinload(Room.images)
            )
            .limit(limit)
        )
        homes = result.scalars().all()

        home_responses = []
        for home in homes:
            # Calculate total images
            total_images = 0
            for room in home.rooms:
                total_images += len(room.images)

            home_responses.append(
                HomeResponse(
                    id=str(home.id),
                    name=home.name,
                    address=home.address,
                    home_type=home.home_type.value if hasattr(home.home_type, 'value') else str(home.home_type),
                    digital_twin_completeness=home.digital_twin_completeness,
                    total_rooms=len(home.rooms),
                    total_images=total_images
                )
            )

        return home_responses

    except Exception as e:
        logger.error(f"Error listing homes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/homes/{home_id}/import-room-images", response_model=ImportRoomImagesResponse)
async def import_room_images(
    home_id: UUID,
    request: ImportRoomImagesRequest = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Scan a directory for room photos, map them to rooms, and analyze.

    This endpoint walks a folder (default 'uploads/room_images'), infers room mapping
    from filename hints, and calls the room image analysis pipeline per image.
    """
    try:
        service = DigitalTwinService()
        summary = await service.import_and_analyze_room_images(
            db=db,
            home_id=home_id,
            directory=(request.directory if request else None)
        )
        return ImportRoomImagesResponse(**summary)
    except Exception as e:
        logger.error(f"Error importing room images: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/homes/{home_id}/ingest-floorplan-json")
async def ingest_floorplan_json(
    home_id: UUID,
    request: IngestFloorplanJsonRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Ingest an existing floor plan analysis JSON into the database (no AI call)."""
    try:
        service = DigitalTwinService()
        result = await service.ingest_floor_plan_from_json(
            db=db,
            home_id=home_id,
            json_path=request.json_path,
            image_url=request.image_url,
            name_prefix=request.name_prefix,
        )
        if result.get("errors"):
            raise HTTPException(status_code=400, detail=result["errors"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting floorplan JSON: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/homes/{home_id}/ingest-image-links-analyses")
async def ingest_image_links_analyses(
    home_id: UUID,
    request: IngestImageLinksAnalysesRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Ingest pre-generated image links and analyses JSON artifacts into the database (no AI call)."""
    try:
        service = DigitalTwinService()
        result = await service.ingest_image_links_and_analyses(
            db=db,
            home_id=home_id,
            links_path=request.links_path,
            analyses_path=request.analyses_path,
            rename_files=request.rename_files,
            score_threshold=request.score_threshold,
        )
        return result
    except Exception as e:
        logger.error(f"Error ingesting image links/analyses: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/homes/{home_id}/bulk-room-images", response_model=BulkUploadResult)
async def bulk_upload_room_images(
    home_id: UUID,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Upload multiple room images, analyze them with AI, auto-link to rooms, and persist.

    This endpoint avoids filename heuristics by analyzing content and ranking against existing rooms.
    Precondition: The home's rooms should already exist (from a floor plan analysis/ingest).
    """
    try:
        # Ensure rooms exist
        from sqlalchemy import select
        rooms_res = await db.execute(select(Room).where(Room.home_id == home_id))
        rooms = rooms_res.scalars().all()
        if not rooms:
            raise HTTPException(status_code=400, detail="No rooms found for home. Analyze/ingest a floor plan first.")

        # Build room index for linking
        room_index: List[dict] = []
        for r in rooms:
            extra = r.extra_data or {}
            room_index.append({
                "id": str(r.id),
                "name": r.name or "",
                "room_type": (r.room_type.value if hasattr(r.room_type, 'value') else str(r.room_type)).lower(),
                "floor_number": r.floor_level,
                "floor_type": None,
                "features": (extra.get("features") or []),
                "label_ocr": extra.get("label_ocr"),
                "measured_dimensions": {"length": r.length, "width": r.width},
            })

        # Helper to map agent output to DB-aligned record
        def map_db_aligned(image_path: str, data: dict) -> dict:
            vc = (data.get("visual_characteristics") or {})
            dims = (data.get("dimensions") or {})
            return {
                "image": image_path,
                "filename": Path(image_path).name,
                "image_analysis": {
                    "description": f"{data.get('room_style', 'unknown')} {data.get('room_type', 'room')}",
                    "keywords": [],
                    "dominant_colors": vc.get("dominant_colors", []),
                    "objects_detected": data.get("detected_products", []),
                    "materials_visible": data.get("detected_materials", []),
                    "fixtures_visible": data.get("detected_fixtures", []),
                    "image_quality_score": None,
                    "lighting_quality": vc.get("lighting_quality"),
                    "clarity": None,
                    "view_angle": None,
                    "estimated_coverage": None,
                    "confidence_score": data.get("confidence_score"),
                    "analysis_model": (data.get("metadata", {}) or {}).get("model_used", "gemini-2.5-flash"),
                    "analysis_notes": (data.get("raw_response", {}) or {}).get("notes", ""),
                },
                "room_analysis": {
                    "room_type_detected": data.get("room_type"),
                    "style": data.get("room_style"),
                    "color_palette": vc.get("color_palette", {}),
                    "overall_condition": (data.get("condition_assessment", {}) or {}).get("overall_condition"),
                    "condition_score": None,
                    "condition_notes": None,
                    "materials_detected": data.get("detected_materials", []),
                    "fixtures_detected": data.get("detected_fixtures", []),
                    "products_detected": data.get("detected_products", []),
                    "improvement_suggestions": data.get("improvement_suggestions", []),
                    "estimated_renovation_priority": None,
                    "confidence_score": data.get("confidence_score"),
                    "analysis_notes": "",
                },
                "extras": {
                    "floor_hint": {},
                    "spatial_cues": {
                        "approx_dimensions_ft": {
                            "length": dims.get("estimated_length_ft"),
                            "width": dims.get("estimated_width_ft"),
                            "height": dims.get("estimated_height_ft"),
                        },
                        "layout_hint": None,
                        "counts": {"windows": None, "doors": None},
                        "adjacency_hints": [],
                    },
                    "name_hint": "",
                }
            }

        # Save files and analyze
        upload_dir = Path("uploads/room_images")
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_paths: List[str] = []
        for f in files:
            if not f.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {f.filename}")
            dest = upload_dir / f.filename
            await save_upload_file(f, dest)
            saved_paths.append(str(dest))

        # Run AI per image
        from backend.agents.digital_twin import RoomAnalysisAgent
        agent = RoomAnalysisAgent()

        analyses: List[dict] = []
        for path in saved_paths:
            resp = await agent.execute({
                "image": path,
                "room_type": "unknown",
                "analysis_type": "comprehensive",
            })
            if not getattr(resp, "success", False):
                logger.warning(f"Analysis failed for {Path(path).name}: {getattr(resp, 'error', 'unknown error')}")
                continue
            analyses.append(map_db_aligned(path, getattr(resp, "data", {}) or {}))

        # Build links via ranking
        links: List[dict] = []
        for rec in analyses:
            ra = rec.get("room_analysis", {}) or {}
            extras = rec.get("extras", {}) or {}
            ia = rec.get("image_analysis", {}) or {}
            # Minimal shape expected by linking
            analysis_for_link = {
                "room_type": (ra.get("room_type_detected") or "other"),
                "floor_hint": (extras.get("floor_hint") or {}),
                "name_hint": extras.get("name_hint") or "",
                "tags": ia.get("keywords") or [],
                "keywords": ia.get("keywords") or [],
                "appliances": [
                    {"type": (p.get("product_type") or p.get("product_category") or ""), "brand": p.get("brand_detected")}
                    for p in (ia.get("objects_detected") or [])
                ],
                "fixtures_visible": ia.get("fixtures_visible") or [],
                "objects_detected": ia.get("objects_detected") or [],
                "description": ia.get("description") or "",
                "spatial_cues": {"approx_dimensions_ft": (extras.get("spatial_cues", {}) or {}).get("approx_dimensions_ft") or {}},
            }
            ranked = rank_candidates(analysis_for_link, room_index)
            links.append({
                "image": rec.get("image"),
                "filename": rec.get("filename"),
                "candidates": ranked[:3] if ranked else [],
            })

        # Persist
        service = DigitalTwinService()
        result = await service.ingest_links_and_analyses_objects(
            db=db,
            home_id=home_id,
            links=links,
            analyses=analyses,
            rename_files=False,
            score_threshold=1.2,  # Slightly lower for UI flow; still skips very low-confidence
        )

        return BulkUploadResult(
            ingested=result.get("ingested", 0),
            skipped=result.get("skipped", 0),
            errors=result.get("errors", []),
            analyses_saved=len(analyses),
            links_built=len(links),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/homes/{home_id}/export-csv")
async def export_home_csv(
    home_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """Export core tables for a home as a ZIP of CSV files for backup."""
    import io
    import csv
    import zipfile
    import json as _json
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        res = await db.execute(
            select(Home)
            .options(
                selectinload(Home.floor_plans),
                selectinload(Home.rooms).selectinload(Room.images),
                selectinload(Home.rooms).selectinload(Room.materials),
                selectinload(Home.rooms).selectinload(Room.fixtures),
                selectinload(Home.rooms).selectinload(Room.products),
            )
            .where(Home.id == home_id)
        )
        home = res.scalar_one_or_none()
        if not home:
            raise HTTPException(status_code=404, detail="Home not found")

        # Collect rows
        floor_plans = [
            {"id": str(fp.id), "home_id": str(home.id), "name": fp.name, "floor_level": fp.floor_level, "image_url": fp.image_url, "scale": fp.scale}
            for fp in home.floor_plans
        ]
        rooms = [
            {"id": str(r.id), "home_id": str(home.id), "name": r.name, "room_type": (r.room_type.value if hasattr(r.room_type,'value') else str(r.room_type)),
             "floor_level": r.floor_level, "length": r.length, "width": r.width, "height": r.height, "area": r.area}
            for r in home.rooms
        ]
        room_images = []
        image_analyses = []
        materials_rows = []
        fixtures_rows = []
        products_rows = []
        floor_plan_analyses_rows = []
        room_analyses_rows = []
        spatial_rows = []
        home_row = [{
            "id": str(home.id),
            "name": home.name,
            "home_type": (home.home_type.value if hasattr(home.home_type, 'value') else str(home.home_type)),
            "year_built": home.year_built,
            "square_footage": home.square_footage,
            "num_bedrooms": home.num_bedrooms,
            "num_bathrooms": home.num_bathrooms,
            "num_floors": home.num_floors,
        }]
        for r in home.rooms:
            for img in r.images:
                room_images.append({
                    "id": str(img.id), "room_id": str(r.id), "image_url": img.image_url, "image_type": img.image_type,
                    "view_angle": img.view_angle, "is_analyzed": img.is_analyzed
                })
    # Query ImageAnalysis by room image ids
        # Build map of analyses per room_image id
        from backend.models import ImageAnalysis as IA, RoomImage as RI
        from sqlalchemy import select as _select
        from uuid import UUID as _UUID
        # room_images list above contains IDs as strings; convert to UUID objects for the query
        img_ids_raw = [ri.get("id") for ri in room_images]
        img_ids: list = []
        for _id in img_ids_raw:
            try:
                img_ids.append(_UUID(_id))
            except Exception:
                # Skip malformed IDs
                continue
        image_analyses_rows = []
        if img_ids:
            iaq = await db.execute(_select(IA).where(IA.room_image_id.in_(img_ids)))
            image_analyses_rows = iaq.scalars().all()
        for ia in image_analyses_rows:
            image_analyses.append({
                "id": str(ia.id),
                "room_image_id": str(ia.room_image_id),
                "description": ia.description,
                "keywords": ",".join(ia.keywords or []),
                "dominant_colors": ",".join(ia.dominant_colors or []),
                "objects_detected": ",".join([str(o) for o in (ia.objects_detected or [])]),
                "materials_visible": ",".join([str(m) for m in (ia.materials_visible or [])]),
                "fixtures_visible": ",".join([str(f) for f in (ia.fixtures_visible or [])]),
                "confidence_score": ia.confidence_score,
                "analysis_model": ia.analysis_model,
            })

        # Additional tables: Materials, Fixtures, Products
        from backend.models import Material as MAT, Fixture as FIX, Product as PROD, FloorPlanAnalysis as FPA, RoomAnalysis as RA, SpatialData as SD
        room_ids = [r["id"] for r in rooms]
        if room_ids:
            from sqlalchemy import select as _sel
            mats_q = await db.execute(_sel(MAT).where(MAT.room_id.in_(room_ids)))
            fixes_q = await db.execute(_sel(FIX).where(FIX.room_id.in_(room_ids)))
            prods_q = await db.execute(_sel(PROD).where(PROD.room_id.in_(room_ids)))
            mats = mats_q.scalars().all()
            fixes = fixes_q.scalars().all()
            prods = prods_q.scalars().all()
            for m in mats:
                materials_rows.append({
                    "id": str(m.id),
                    "room_id": str(m.room_id),
                    "category": (m.category.value if hasattr(m.category, 'value') else str(m.category)),
                    "material_type": m.material_type,
                    "brand": m.brand,
                    "color": m.color,
                    "finish": m.finish,
                    "condition": (m.condition.value if hasattr(m.condition, 'value') else str(m.condition)) if m.condition else None,
                    "estimated_age_years": m.estimated_age_years,
                    "extra_data": _json.dumps(m.extra_data or {}),
                })
            for f in fixes:
                fixtures_rows.append({
                    "id": str(f.id),
                    "room_id": str(f.room_id),
                    "fixture_type": (f.fixture_type.value if hasattr(f.fixture_type, 'value') else str(f.fixture_type)),
                    "brand": f.brand,
                    "model": f.model,
                    "style": f.style,
                    "finish": f.finish,
                    "location": _json.dumps(f.location or {}),
                    "condition": (f.condition.value if hasattr(f.condition, 'value') else str(f.condition)) if f.condition else None,
                    "estimated_age_years": f.estimated_age_years,
                    "extra_data": _json.dumps(f.extra_data or {}),
                })
            for p in prods:
                products_rows.append({
                    "id": str(p.id),
                    "room_id": str(p.room_id),
                    "product_category": p.product_category,
                    "product_type": p.product_type,
                    "brand": p.brand,
                    "style": p.style,
                    "color": p.color,
                    "material": p.material,
                    "dimensions": _json.dumps(p.dimensions or {}),
                    "confidence_score": p.confidence_score,
                    "condition": p.condition,
                    "extra_data": _json.dumps(p.extra_data or {}),
                })

        # FloorPlanAnalyses for this home's floor plans
        fp_ids = [fp["id"] for fp in floor_plans]
        if fp_ids:
            from sqlalchemy import select as _sel
            fpa_q = await db.execute(_sel(FPA).where(FPA.floor_plan_id.in_(fp_ids)))
            fpas = fpa_q.scalars().all()
            for fpa in fpas:
                floor_plan_analyses_rows.append({
                    "id": str(fpa.id),
                    "floor_plan_id": str(fpa.floor_plan_id),
                    "room_count": fpa.room_count,
                    "layout_type": fpa.layout_type,
                    "total_area": fpa.total_area,
                    "features": ",".join(fpa.features or []),
                    "scale_info": _json.dumps(fpa.scale_info or {}),
                    "overall_dimensions": _json.dumps(fpa.overall_dimensions or {}),
                    "detected_rooms": _json.dumps(fpa.detected_rooms or []),
                    "confidence_score": fpa.confidence_score,
                    "analysis_notes": fpa.analysis_notes,
                })
        
        # Optional: RoomAnalyses and SpatialData if present for these rooms
        if room_ids:
            try:
                from sqlalchemy import select as _sel
                ra_q = await db.execute(_sel(RA).where(RA.room_id.in_(room_ids)))
                ras = ra_q.scalars().all()
                for ra in ras:
                    room_analyses_rows.append({
                        "id": str(ra.id),
                        "room_id": str(ra.room_id),
                        "analysis_type": getattr(ra, 'analysis_type', None),
                        "summary": getattr(ra, 'summary', None),
                        "details": _json.dumps(getattr(ra, 'details', None) or {}),
                        "confidence_score": getattr(ra, 'confidence_score', None),
                    })
            except Exception:
                pass
            try:
                from sqlalchemy import select as _sel
                sd_q = await db.execute(_sel(SD).where(SD.room_id.in_(room_ids)))
                sds = sd_q.scalars().all()
                for sd in sds:
                    spatial_rows.append({
                        "id": str(sd.id),
                        "room_id": str(sd.room_id),
                        "layout_type": getattr(sd, 'layout_type', None),
                        "floor_number": getattr(sd, 'floor_number', None),
                        "position": _json.dumps(getattr(sd, 'position', None) or {}),
                        "dimensions": _json.dumps(getattr(sd, 'dimensions', None) or {}),
                        "metadata": _json.dumps(getattr(sd, 'metadata', None) or {}),
                    })
            except Exception:
                pass

        # ZIP CSVs
        mem = io.BytesIO()
        with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            def write_csv(name: str, rows: List[dict]):
                buf = io.StringIO()
                if rows:
                    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    for r in rows:
                        writer.writerow(r)
                else:
                    writer = csv.DictWriter(buf, fieldnames=["empty"])
                    writer.writeheader()
                zf.writestr(name, buf.getvalue())

            write_csv("home.csv", home_row)
            write_csv("floor_plans.csv", floor_plans)
            write_csv("rooms.csv", rooms)
            write_csv("room_images.csv", room_images)
            write_csv("image_analyses.csv", image_analyses)
            write_csv("floor_plan_analyses.csv", floor_plan_analyses_rows)
            write_csv("materials.csv", materials_rows)
            write_csv("fixtures.csv", fixtures_rows)
            write_csv("products.csv", products_rows)
            write_csv("room_analyses.csv", room_analyses_rows)
            write_csv("spatial_data.csv", spatial_rows)

        mem.seek(0)
        headers = {
            "Content-Disposition": f"attachment; filename=home_{home_id}_export.zip"
        }
        return StreamingResponse(mem, media_type="application/zip", headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/homes", response_model=HomeResponse, status_code=201)
async def create_home(
    request: CreateHomeRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new home.
    
    This endpoint creates a new home record in the database.
    """
    try:
        # Find or create user
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == request.owner_email))
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(
                email=request.owner_email,
                user_type=UserType.HOMEOWNER,
                is_active=True
            )
            db.add(user)
            await db.flush()
        
        # Create home
        home = Home(
            owner_id=user.id,
            name=request.name,
            address=request.address,
            home_type=HomeType[request.home_type.upper()],
            year_built=request.year_built,
            square_footage=request.square_footage,
            num_bedrooms=request.num_bedrooms,
            num_bathrooms=request.num_bathrooms,
            num_floors=request.num_floors
        )
        db.add(home)
        await db.commit()
        await db.refresh(home)
        
        logger.info(f"Created home {home.id} for user {user.email}")
        
        return HomeResponse(
            id=str(home.id),
            name=home.name,
            address=home.address,
            home_type=home.home_type.value,
            digital_twin_completeness=home.digital_twin_completeness,
            total_rooms=0,
            total_images=0
        )
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating home: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/homes/{home_id}/floor-plans", response_model=FloorPlanUploadResponse)
async def upload_floor_plan(
    home_id: UUID,
    file: UploadFile = File(...),
    floor_level: int = Form(1),
    scale: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Upload and analyze a floor plan.
    
    This endpoint:
    1. Saves the uploaded floor plan image
    2. Runs AI analysis to extract room layouts
    3. Creates room records in the database
    4. Returns the analysis results
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file
        upload_dir = Path("uploads/floor_plans")
        file_extension = Path(file.filename).suffix
        file_path = upload_dir / f"{home_id}_{floor_level}{file_extension}"
        
        saved_path = await save_upload_file(file, file_path)
        logger.info(f"Saved floor plan to {saved_path}")
        
        # Run analysis
        service = DigitalTwinService()
        result = await service.analyze_and_save_floor_plan(
            db=db,
            home_id=home_id,
            image_path=saved_path,
            floor_level=floor_level,
            scale=scale,
            name=name or f"Floor {floor_level}"
        )
        
        logger.info(f"Floor plan analysis complete: {result['rooms_created']} rooms created")
        
        analysis = result.get("analysis", {})
        units = analysis.get("units", {}) if isinstance(analysis, dict) else {}
        # Prefer explicit floor_plan_id; otherwise, take the first from floor_plan_ids
        primary_fp_id = result.get("floor_plan_id") or (result.get("floor_plan_ids") or [None])[0]
        return FloorPlanUploadResponse(
            floor_plan_id=primary_fp_id,
            floor_plan_ids=result.get("floor_plan_ids"),
            rooms_created=result["rooms_created"],
            room_ids=result["room_ids"],
            message=(
                f"Successfully analyzed multi-floor sheet into {len(result.get('floor_plan_ids') or [])} floor plans; created {result['rooms_created']} rooms"
                if result.get("floor_plan_ids") else
                f"Successfully analyzed floor plan and created {result['rooms_created']} rooms"
            ),
            multi_floor=bool(result.get("floor_plan_ids")),
            sheet_id=result.get("sheet_id"),
            floor_level=analysis.get("floor_level_number"),
            floor_level_name=analysis.get("floor_level_name"),
            scale_text=units.get("scale_text")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading floor plan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rooms/{room_id}/images", response_model=RoomImageUploadResponse)
async def upload_room_image(
    room_id: UUID,
    file: UploadFile = File(...),
    image_type: str = Form("original"),
    view_angle: Optional[str] = Form(None),
    analysis_type: str = Form("comprehensive"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Upload and analyze a room image.
    
    This endpoint:
    1. Saves the uploaded room image
    2. Runs AI analysis to extract materials, fixtures, products
    3. Creates entity records in the database
    4. Returns the analysis results
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Verify room exists
        from sqlalchemy import select
        result = await db.execute(select(Room).where(Room.id == room_id))
        room = result.scalar_one_or_none()
        if not room:
            raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
        
        # Save uploaded file
        upload_dir = Path("uploads/room_images")
        file_extension = Path(file.filename).suffix
        file_path = upload_dir / f"{room_id}_{uuid_lib.uuid4()}{file_extension}"
        
        saved_path = await save_upload_file(file, file_path)
        logger.info(f"Saved room image to {saved_path}")
        
        # Run analysis
        service = DigitalTwinService()
        result = await service.analyze_and_save_room_image(
            db=db,
            room_id=room_id,
            image_path=saved_path,
            image_type=image_type,
            view_angle=view_angle,
            analysis_type=analysis_type
        )
        
        logger.info(f"Room image analysis complete: {result['materials_created']} materials, "
                   f"{result['fixtures_created']} fixtures, {result['products_created']} products")
        
        return RoomImageUploadResponse(
            image_id=result["image_id"],
            materials_created=result["materials_created"],
            fixtures_created=result["fixtures_created"],
            products_created=result["products_created"],
            message=f"Successfully analyzed room image"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading room image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/homes/{home_id}", response_model=DigitalTwinResponse)
async def get_home_digital_twin(
    home_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get complete digital twin data for a home.
    
    This endpoint retrieves all data associated with a home including:
    - Basic home information
    - Floor plans
    - Rooms with dimensions
    - Materials, fixtures, products
    - Analysis results
    """
    try:
        service = DigitalTwinService()
        digital_twin = await service.get_home_digital_twin(db, home_id)
        
        return DigitalTwinResponse(**digital_twin)
    
    except Exception as e:
        logger.error(f"Error retrieving digital twin: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/homes/{home_id}/rooms", response_model=List[dict])
async def get_home_rooms(
    home_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """Get all rooms for a home."""
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(Room)
            .options(
                selectinload(Room.images),
                selectinload(Room.materials),
                selectinload(Room.fixtures),
                selectinload(Room.products)
            )
            .where(Room.home_id == home_id)
        )
        rooms = result.scalars().all()
        
        return [
            {
                "id": str(room.id),
                "name": room.name,
                "room_type": room.room_type,
                "floor_level": room.floor_level,
                "dimensions": {
                    "length": room.length,
                    "width": room.width,
                    "height": room.height,
                    "area": room.area
                },
                "images_count": len(room.images),
                "materials_count": len(room.materials),
                "fixtures_count": len(room.fixtures),
                "products_count": len(room.products)
            }
            for room in rooms
        ]
    
    except Exception as e:
        logger.error(f"Error retrieving rooms: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rooms/{room_id}", response_model=dict)
async def get_room_details(
    room_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """Get detailed information about a specific room."""
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(Room)
            .options(
                selectinload(Room.images),
                selectinload(Room.materials),
                selectinload(Room.fixtures),
                selectinload(Room.products),
                selectinload(Room.spatial_data)
            )
            .where(Room.id == room_id)
        )
        room = result.scalar_one_or_none()
        
        if not room:
            raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
        
        return {
            "id": str(room.id),
            "name": room.name,
            "room_type": room.room_type,
            "floor_level": room.floor_level,
            "dimensions": {
                "length": room.length,
                "width": room.width,
                "height": room.height,
                "area": room.area
            },
            "condition_score": room.condition_score,
            "images": [
                {
                    "id": str(img.id),
                    "image_url": img.image_url,
                    "image_type": img.image_type,
                    "view_angle": img.view_angle,
                    "is_analyzed": img.is_analyzed
                }
                for img in room.images
            ],
            "materials": [
                {
                    "id": str(mat.id),
                    "category": mat.category,
                    "material_type": mat.material_type,
                    "brand": mat.brand,
                    "color": mat.color,
                    "condition": mat.condition
                }
                for mat in room.materials
            ],
            "fixtures": [
                {
                    "id": str(fix.id),
                    "fixture_type": fix.fixture_type,
                    "brand": fix.brand,
                    "style": fix.style,
                    "condition": fix.condition
                }
                for fix in room.fixtures
            ],
            "products": [
                {
                    "id": str(prod.id),
                    "product_type": prod.product_type,
                    "brand": prod.brand,
                    "style": prod.style,
                    "condition": prod.condition
                }
                for prod in room.products
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving room details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/unknown-room-types")
async def get_unknown_room_types_endpoint():
    """
    Get all unknown room types encountered by the system.

    This endpoint helps administrators identify new room types that should
    be added to the RoomType enum or synonym mappings.

    Returns:
        List of unknown room type strings
    """
    try:
        unknown_types = get_unknown_room_types()
        return {
            "unknown_room_types": list(unknown_types),
            "count": len(unknown_types),
            "message": "These room types were detected but not recognized. Consider adding them to the enum or synonyms."
        }
    except Exception as e:
        logger.error(f"Error retrieving unknown room types: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class AddSynonymRequest(BaseModel):
    """Request model for adding a room type synonym."""
    synonym: str = Field(..., description="The synonym to add (e.g., 'breakfast nook')")
    target: str = Field(..., description="The target RoomType enum value (e.g., 'dining_area')")


@router.post("/admin/add-room-type-synonym")
async def add_room_type_synonym_endpoint(request: AddSynonymRequest):
    """
    Add a new room type synonym mapping.

    This allows administrators to teach the system new room type variations
    without modifying the code.

    Args:
        request: Synonym and target room type

    Returns:
        Success message
    """
    try:
        add_room_type_synonym(request.synonym, request.target)
        return {
            "success": True,
            "message": f"Added synonym mapping: '{request.synonym}' -> '{request.target}'"
        }
    except Exception as e:
        logger.error(f"Error adding room type synonym: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Chat Endpoints
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str = Field(..., description="User's message/question")
    home_id: Optional[str] = Field(None, description="Home ID for context")
    conversation_history: Optional[List[dict]] = Field(None, description="Previous conversation messages")


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    response: str = Field(..., description="AI-generated response")
    timestamp: str = Field(..., description="Response timestamp")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Chat with HomeVision AI about your home.

    Args:
        request: Chat request with message and optional home context

    Returns:
        AI-generated response based on home data
    """
    try:
        from datetime import datetime

        # Fetch home data if home_id provided
        home_data = None
        if request.home_id:
            try:
                home_uuid = UUID(request.home_id)
                service = DigitalTwinService()
                home_data = await service.get_home_digital_twin(db, home_uuid)
                logger.info(f"Fetched home data for chat: {home_data.get('home_id')}")
            except Exception as e:
                logger.warning(f"Could not fetch home data: {str(e)}")

        # Lazy import to avoid loading heavy dependencies during startup
        from backend.agents.conversational import process_chat_message

        # Process chat message
        response_text = await process_chat_message(
            user_message=request.message,
            home_data=home_data,
            conversation_history=request.conversation_history
        )

        return ChatResponse(
            response=response_text,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )

