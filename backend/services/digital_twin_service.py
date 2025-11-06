"""Digital Twin Service - Orchestrates analysis and data persistence."""

import logging
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from backend.models import (
    Home, Room, RoomImage, FloorPlan, SpatialData,
    Material, Fixture, Product,
    FloorPlanAnalysis, RoomAnalysis, ImageAnalysis
)
from backend.agents.digital_twin import FloorPlanAnalysisAgent, RoomAnalysisAgent
from backend.utils.image_filename_parser import parse_image_filename
from backend.utils.room_type_normalizer import normalize_room_type

logger = logging.getLogger(__name__)


class DigitalTwinService:
    """Service layer for analyzing and persisting digital twin data."""

    def __init__(self) -> None:
        # Initialize analysis agents used by this service
        self.floor_plan_agent = FloorPlanAnalysisAgent()
        self.room_analysis_agent = RoomAnalysisAgent()

    async def analyze_and_save_floor_plan(
        self,
        db: AsyncSession,
        home_id: uuid.UUID,
        image_path: str,
        floor_level: int = 1,
        scale: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze a floor plan image (single or multi-floor) and persist FloorPlans, Rooms, and FloorPlanAnalysis.

        Returns a payload containing created floor_plan_ids, room_ids, rooms_created, and sheet_id (if multi-floor).
        """
        try:
            # Run AI analysis via the floor plan agent
            resp = await self.floor_plan_agent.execute({
                "image": image_path,
                "floor_level": floor_level,
                "scale": scale,
                "name": name or f"Floor {floor_level}",
            })
            if not getattr(resp, "success", False):
                raise RuntimeError(getattr(resp, "error", "Floor plan analysis failed"))

            data = getattr(resp, "data", {}) or {}
            floors = data.get("floors") or []
            is_multi = bool(floors)
            if not is_multi:
                # Treat as single-floor; synthesize floors list from top-level keys if provided
                floors = [{
                    "floor_level_number": data.get("floor_level_number") or data.get("floor_number") or floor_level,
                    "floor_level_name": data.get("floor_level_name") or data.get("floor_name") or None,
                    "units": data.get("units") or {},
                    "pixel_to_unit": data.get("pixel_to_unit"),
                    "section_bbox": data.get("section_bbox"),
                    "rooms": data.get("rooms") or data.get("detected_rooms") or [],
                    "layout_analysis": data.get("layout_analysis") or {},
                    "confidence_metrics": data.get("confidence_metrics") or {},
                }]

            sheet_id = str(uuid.uuid4()) if is_multi else None

            created_room_ids: list[str] = []
            created_fp_ids: list[str] = []

            for idx, fl in enumerate(floors):
                fl_num = fl.get("floor_level_number")
                if fl_num is None:
                    fl_num = fl.get("floor_number")
                try:
                    fl_num_int = int(fl_num) if fl_num is not None else int(floor_level)
                except Exception:
                    fl_num_int = int(floor_level)

                fl_name = fl.get("floor_level_name") or fl.get("floor_name") or name or f"Floor {fl_num_int}"
                units = fl.get("units") or (data.get("units") or {})
                scale_text = (units or {}).get("scale_text") or scale

                # Create FloorPlan
                fp = FloorPlan(
                    home_id=home_id,
                    name=f"{fl_name} (section {idx+1})" if is_multi else fl_name,
                    floor_level=fl_num_int,
                    image_url=str(image_path),
                    scale=scale_text,
                    is_analyzed=True,
                    analysis_metadata={
                        "sheet_id": sheet_id,
                        "section_index": idx,
                        "source_image": str(image_path),
                    }
                )
                db.add(fp)
                await db.flush()
                created_fp_ids.append(str(fp.id))

                # Persist FloorPlanAnalysis
                rooms_arr = fl.get("rooms") or fl.get("detected_rooms") or []
                layout = fl.get("layout_analysis", {}) or {}
                scale_info = {
                    "units": units,
                    "pixel_to_unit": fl.get("pixel_to_unit"),
                    "section_bbox": fl.get("section_bbox"),
                }
                fpa = FloorPlanAnalysis(
                    floor_plan_id=fp.id,
                    detected_rooms=rooms_arr,
                    room_count=len(rooms_arr),
                    total_area=layout.get("total_area_sqft", 0.0),
                    layout_type=layout.get("layout_type", "unknown"),
                    spatial_efficiency=0.0,
                    architectural_style="unknown",
                    features=[],
                    scale_info=scale_info,
                    overall_dimensions={},
                    confidence_score=(fl.get("confidence_metrics", {}) or {}).get("overall_confidence", 1.0 if rooms_arr else 0.0),
                    analysis_notes="AI-generated analysis",
                )
                db.add(fpa)

                # Persist Rooms
                for r in rooms_arr:
                    dims = r.get("measured_dimensions") or r.get("dimensions") or {}
                    length_ft = (dims.get("length") or {}).get("value")
                    width_ft = (dims.get("width") or {}).get("value")
                    area_sqft = (dims.get("area") or {}).get("value") or (dims.get("area_sqft") if isinstance(dims, dict) else None)

                    rt_norm = normalize_room_type(r.get("room_type") or "other")
                    room = Room(
                        home_id=home_id,
                        name=r.get("name") or r.get("id") or "Unnamed Room",
                        room_type=rt_norm,
                        floor_level=fl_num_int,
                        floor_plan_id=fp.id,
                        length=length_ft,
                        width=width_ft,
                        area=area_sqft,
                        extra_data={
                            "detected_from_floor_plan": True,
                            "floor_plan_id": str(fp.id),
                            "features": r.get("features", []),
                            "location": {
                                "polygon": r.get("polygon"),
                                "centroid": r.get("centroid"),
                            },
                            "confidence": r.get("confidence", 0.0),
                            "label_ocr": r.get("label_ocr"),
                        }
                    )
                    db.add(room)
                    await db.flush()
                    created_room_ids.append(str(room.id))

            await db.commit()
            return {
                "floor_plan_ids": created_fp_ids,
                "room_ids": created_room_ids,
                "rooms_created": len(created_room_ids),
                "sheet_id": sheet_id,
                "analysis": data,
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Error in analyze_and_save_floor_plan: {e}", exc_info=True)
            raise

    async def analyze_and_save_room_image(
        self,
        db: AsyncSession,
        room_id: uuid.UUID,
        image_path: str,
        view_angle: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze a single room image with AI and persist results to the DB.

        Creates RoomImage, ImageAnalysis, Materials, Fixtures and Products.
        """
        try:
            # Verify room exists
            result = await db.execute(select(Room).where(Room.id == room_id))
            room = result.scalar_one_or_none()
            if not room:
                raise ValueError(f"Room {room_id} not found")

            # Create RoomImage record
            room_image = RoomImage(
                room_id=room_id,
                image_url=image_path,
                image_type="original",
                view_angle=view_angle,
                is_analyzed=True,
                analysis_metadata={},
            )
            db.add(room_image)
            await db.flush()

            # Run AI analysis
            ai_resp = await self.room_analysis_agent.execute({
                "image": image_path,
                "room_type": room.room_type.value if hasattr(room.room_type, 'value') else str(room.room_type),
                "analysis_type": "comprehensive",
            })

            if not ai_resp.success:
                raise RuntimeError(ai_resp.error or "Room analysis failed")

            analysis_data = ai_resp.data or {}

            # Create ImageAnalysis
            img_analysis = ImageAnalysis(
                room_image_id=room_image.id,
                description=f"{analysis_data.get('room_style', 'unknown')} {analysis_data.get('room_type', 'room')}",
                keywords=analysis_data.get("keywords", []),
                dominant_colors=analysis_data.get("visual_characteristics", {}).get("dominant_colors", []),
                objects_detected=analysis_data.get("detected_products", []),
                materials_visible=analysis_data.get("detected_materials", []),
                fixtures_visible=analysis_data.get("detected_fixtures", []),
                image_quality_score=0.8,  # Could be calculated from image properties
                lighting_quality=analysis_data.get("visual_characteristics", {}).get("lighting_quality", "good"),
                clarity="sharp",
                view_angle=view_angle or "front",
                estimated_coverage=0.8,
                confidence_score=analysis_data.get("confidence_score", 0.0),
                analysis_model=analysis_data.get("metadata", {}).get("model_used", "gemini-2.5-flash"),
                analysis_notes=analysis_data.get("analysis_notes", ""),
            )
            db.add(img_analysis)

            # Create Material records
            materials_created = []
            for mat_data in (analysis_data.get("detected_materials", []) or []):
                material = Material(
                    room_id=room_id,
                    category=mat_data.get("category", "other"),
                    material_type=mat_data.get("material_type", "unknown"),
                    brand=mat_data.get("brand_detected"),
                    color=mat_data.get("color"),
                    finish=mat_data.get("finish"),
                    condition=mat_data.get("condition", "unknown"),
                    extra_data={
                        "detected_from_image": str(room_image.id),
                        "confidence": mat_data.get("confidence", 0.0),
                        "coverage_area": mat_data.get("coverage_area"),
                    },
                )
                db.add(material)
                materials_created.append(material)

            # Create Fixture records
            fixtures_created = []
            for fix_data in (analysis_data.get("detected_fixtures", []) or []):
                fixture = Fixture(
                    room_id=room_id,
                    fixture_type=fix_data.get("fixture_type", "unknown"),
                    brand=fix_data.get("brand_detected"),
                    model=fix_data.get("model_detected"),
                    style=fix_data.get("style"),
                    finish=fix_data.get("finish"),
                    location=fix_data.get("location"),
                    condition=fix_data.get("condition", "unknown"),
                    extra_data={
                        "detected_from_image": str(room_image.id),
                        "confidence": fix_data.get("confidence", 0.0),
                    },
                )
                db.add(fixture)
                fixtures_created.append(fixture)

            # Create Product records
            products_created = []
            for prod_data in (analysis_data.get("detected_products", []) or []):
                product = Product(
                    room_id=room_id,
                    product_category=prod_data.get("product_category", "unknown"),
                    product_type=prod_data.get("product_type", "unknown"),
                    brand=prod_data.get("brand_detected"),
                    style=prod_data.get("style"),
                    color=prod_data.get("color"),
                    material=prod_data.get("material"),
                    dimensions=prod_data.get("estimated_dimensions", {}),
                    confidence_score=prod_data.get("confidence", 0.0),
                    condition=prod_data.get("condition", "unknown"),
                    extra_data={
                        "detected_from_image": str(room_image.id),
                    },
                )
                db.add(product)
                products_created.append(product)

            # Update room dimensions if detected and not already set
            if not room.length and analysis_data.get("dimensions"):
                dims = analysis_data["dimensions"]
                room.length = dims.get("estimated_length_ft")
                room.width = dims.get("estimated_width_ft")
                room.height = dims.get("estimated_height_ft")
                room.area = dims.get("estimated_area_sqft")

            await db.commit()

            logger.info(
                f"Successfully saved room image analysis with {len(materials_created)} materials, "
                f"{len(fixtures_created)} fixtures, {len(products_created)} products"
            )

            return {
                "image_id": str(room_image.id),
                "analysis": analysis_data,
                "materials_created": len(materials_created),
                "fixtures_created": len(fixtures_created),
                "products_created": len(products_created),
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Error in analyze_and_save_room_image: {str(e)}", exc_info=True)
            raise

    async def import_and_analyze_room_images(
        self,
        db: AsyncSession,
        home_id: uuid.UUID,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Scan a directory for room images, map them to rooms, and analyze them.

        Mapping heuristics (in order):
        - Filename contains a specific room name (substring match, case-insensitive).
        - Filename-derived room_type and/or floor level narrows candidates.
        - If still ambiguous, prefer single candidate by room_type; otherwise skip and report.
        """
        import os

        base_dir = directory or os.path.join("uploads", "room_images")
        if not os.path.isdir(base_dir):
            return {"total_found": 0, "matched": 0, "analyzed": 0, "skipped": 0, "errors": [f"Directory not found: {base_dir}"]}

        # Load rooms for the home
        result = await db.execute(select(Room).where(Room.home_id == home_id))
        rooms = result.scalars().all()
        if not rooms:
            return {"total_found": 0, "matched": 0, "analyzed": 0, "skipped": 0, "errors": ["No rooms found for home; run floor plan analysis first." ]}

        def norm(s: str) -> str:
            return "".join(ch for ch in s.lower() if ch.isalnum())

        room_index_by_name = {norm(r.name): r for r in rooms if r.name}

        # Walk directory
        allowed = {".jpg", ".jpeg", ".png", ".webp"}
        files: list[str] = []
        for root, _dirs, filenames in os.walk(base_dir):
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in allowed:
                    files.append(os.path.join(root, fn))

        matched = 0
        analyzed = 0
        skipped = 0
        errors: list[str] = []

        # Helper to choose best candidate room
        def choose_room(path: str) -> Optional[Room]:
            hints = parse_image_filename(path)
            base = os.path.basename(path)
            nb = norm(base)

            # Name-based direct match
            for key, r in room_index_by_name.items():
                if key and key in nb:
                    return r

            # Type/Floor filtered candidates
            candidates = rooms
            if hints.get("room_type"):
                candidates = [r for r in candidates if hasattr(r.room_type, 'value') and r.room_type.value == hints["room_type"] or str(r.room_type) == hints["room_type"]]
            if hints.get("floor_level") is not None:
                candidates = [r for r in candidates if r.floor_level == hints["floor_level"]]

            if len(candidates) == 1:
                return candidates[0]
            return None

        for path in files:
            try:
                room = choose_room(path)
                if not room:
                    skipped += 1
                    continue
                matched += 1
                # Store and analyze
                res = await self.analyze_and_save_room_image(db, room.id, path)
                if res.get("image_id"):
                    analyzed += 1
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")

        return {
            "directory": base_dir,
            "total_found": len(files),
            "matched": matched,
            "analyzed": analyzed,
            "skipped": skipped,
            "errors": errors,
        }

    async def ingest_floor_plan_from_json(
        self,
        db: AsyncSession,
        home_id: uuid.UUID,
        json_path: str,
        image_url: Optional[str] = None,
        name_prefix: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ingest a floor plan analysis JSON (single or multi-floor) and persist rooms.

        The JSON structure is expected to include either:
        - multi-floor: { floors: [ { floor_number, floor_name, section_bbox, pixel_to_unit, rooms: [...] }, ... ], units: {...} }
        - single-floor: { floor_level_number|floor_number, floor_level_name|floor_name, detected_rooms|rooms: [...] }
        """
        p = Path(json_path)
        if not p.exists():
            return {"floor_plan_ids": [], "rooms_created": 0, "errors": [f"JSON not found: {json_path}"]}

        with open(p, "r", encoding="utf-8") as f:
            doc = json.load(f)

        # Decide multi-floor vs single-floor
        floors = doc.get("floors")
        is_multi = isinstance(floors, list) and len(floors) > 0
        sheet_id = str(uuid.uuid4()) if is_multi else None

        created_rooms: list[Room] = []
        floor_plan_ids: list[str] = []

        top_units = doc.get("units") or {}

        def pick(val, alt_keys: list[str], default=None):
            if val is not None:
                return val
            for k in alt_keys:
                v = doc.get(k)
                if v is not None:
                    return v
            return default

        async def _create_for_floor(floor_payload: dict, section_index: int = 0):
            nonlocal created_rooms, floor_plan_ids
            # Determine level and name
            fl_num = floor_payload.get("floor_level_number")
            if fl_num is None:
                fl_num = floor_payload.get("floor_number")
            fl_name = floor_payload.get("floor_level_name") or floor_payload.get("floor_name")

            # Name and scale
            units = floor_payload.get("units") or top_units
            scale_text = (units or {}).get("scale_text")

            # Create FloorPlan row
            fp = FloorPlan(
                home_id=home_id,
                name=(name_prefix + " - " if name_prefix else "") + (fl_name or f"Floor {fl_num if fl_num is not None else 1}") + (f" (section {section_index+1})" if is_multi else ""),
                floor_level=fl_num if isinstance(fl_num, int) else 1,
                image_url=image_url or str(p),
                scale=scale_text,
                is_analyzed=True,
                analysis_metadata={
                    "sheet_id": sheet_id,
                    "section_index": section_index,
                    "source_json": str(p),
                }
            )
            db.add(fp)
            await db.flush()
            floor_plan_ids.append(str(fp.id))

            # Prepare FloorPlanAnalysis
            rooms_arr = floor_payload.get("rooms") or floor_payload.get("detected_rooms") or []
            layout = floor_payload.get("layout_analysis", {}) or {}
            scale_info = {
                "units": units,
                "pixel_to_unit": floor_payload.get("pixel_to_unit"),
                "section_bbox": floor_payload.get("section_bbox"),
            }

            fp_analysis = FloorPlanAnalysis(
                floor_plan_id=fp.id,
                detected_rooms=rooms_arr,
                room_count=len(rooms_arr),
                total_area=layout.get("total_area_sqft", 0.0),
                layout_type=layout.get("layout_type", "unknown"),
                spatial_efficiency=0.0,
                architectural_style="unknown",
                features=[],
                scale_info=scale_info,
                overall_dimensions={},
                confidence_score=1.0 if rooms_arr else 0.0,
                analysis_notes="Imported from JSON"
            )
            db.add(fp_analysis)

            # Create Room rows
            for r in rooms_arr:
                dims = r.get("measured_dimensions") or r.get("dimensions") or {}
                length_ft = (dims.get("length") or {}).get("value")
                width_ft = (dims.get("width") or {}).get("value")
                area_sqft = (dims.get("area") or {}).get("value")

                rt_raw = r.get("room_type") or "other"
                rt_norm = normalize_room_type(rt_raw)

                room = Room(
                    home_id=home_id,
                    name=r.get("name") or r.get("id") or "Unnamed Room",
                    room_type=rt_norm,
                    floor_level=fp.floor_level,
                    floor_plan_id=fp.id,
                    length=length_ft,
                    width=width_ft,
                    area=area_sqft,
                    extra_data={
                        "detected_from_floor_plan": True,
                        "floor_plan_id": str(fp.id),
                        "features": r.get("features", []),
                        "location": {
                            "polygon": r.get("polygon"),
                            "centroid": r.get("centroid"),
                        },
                        "confidence": r.get("confidence", 0.0),
                        "label_ocr": r.get("label_ocr"),
                    }
                )
                db.add(room)
                created_rooms.append(room)

        try:
            if is_multi:
                for idx, fl in enumerate(floors):
                    await _create_for_floor(fl, section_index=idx)
            else:
                await _create_for_floor(doc, section_index=0)

            await db.commit()
            return {
                "floor_plan_ids": floor_plan_ids,
                "rooms_created": len(created_rooms),
                "sheet_id": sheet_id,
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Error ingesting floor plan JSON: {e}", exc_info=True)
            return {"floor_plan_ids": [], "rooms_created": 0, "errors": [str(e)]}

    async def analyze_room_images_to_json(
        self,
        db: AsyncSession,
        home_id: uuid.UUID,
        directory: Optional[str] = None,
        analysis_type: str = "comprehensive",
        output_path: Optional[str] = None,
        overwrite: bool = True,
    ) -> Dict[str, Any]:
        """Scan a directory for room images, run AI analysis ONCE, and write results to a JSON file.

        This does NOT persist anything to the database. It prepares a consolidated JSON
        payload for manual review and later ingestion.
        """
        base_dir = directory or os.path.join("uploads", "room_images")
        if not os.path.isdir(base_dir):
            return {"output_path": None, "total_found": 0, "analyzed": 0, "skipped": 0, "errors": [f"Directory not found: {base_dir}"]}

        # Load rooms for mapping context
        result = await db.execute(select(Room).where(Room.home_id == home_id))
        rooms = result.scalars().all()

        def norm(s: str) -> str:
            return "".join(ch for ch in s.lower() if ch.isalnum())

        room_index_by_name = {norm(r.name): r for r in rooms if r.name}

        # Collect image files
        allowed = {".jpg", ".jpeg", ".png", ".webp"}
        files: list[str] = []
        for root, _dirs, filenames in os.walk(base_dir):
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in allowed:
                    files.append(os.path.join(root, fn))

        # Helper to choose best candidate room (same heuristic as import)
        def choose_room(path: str) -> Optional[Room]:
            hints = parse_image_filename(path)
            base = os.path.basename(path)
            nb = norm(base)

            # Name-based direct match
            for key, r in room_index_by_name.items():
                if key and key in nb:
                    return r

            # Type/Floor filtered candidates
            candidates = rooms
            if hints.get("room_type"):
                candidates = [r for r in candidates if (hasattr(r.room_type, 'value') and r.room_type.value == hints["room_type"]) or (str(r.room_type) == hints["room_type"]) ]
            if hints.get("floor_level") is not None:
                candidates = [r for r in candidates if r.floor_level == hints["floor_level"]]

            if len(candidates) == 1:
                return candidates[0]
            return None

        analyzed = 0
        skipped = 0
        errors: list[str] = []
        outputs: list[dict] = []

        # Ensure output path
        out_path = Path(output_path or os.path.join(base_dir, "analysis_report.json"))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and not overwrite:
            return {"output_path": str(out_path), "total_found": len(files), "analyzed": 0, "skipped": len(files), "errors": ["Output exists and overwrite is False"]}

        # Process each image with AI (no DB writes)
        for path in files:
            try:
                room = choose_room(path)
                room_type_hint = room.room_type.value if (room and hasattr(room.room_type, 'value')) else (str(room.room_type) if room else None)

                ai_resp = await self.room_analysis_agent.execute({
                    "image": path,
                    "room_type": room_type_hint or "unknown",
                    "analysis_type": analysis_type,
                })

                if not ai_resp.success:
                    skipped += 1
                    errors.append(f"{os.path.basename(path)}: {ai_resp.error}")
                    continue

                analyzed += 1

                outputs.append({
                    "home_id": str(home_id),
                    "image_path": path,
                    "filename_hints": parse_image_filename(path),
                    "mapped_room": ({
                        "id": str(room.id),
                        "name": room.name,
                        "room_type": room.room_type.value if hasattr(room.room_type, 'value') else str(room.room_type),
                        "floor_level": room.floor_level,
                    } if room else None),
                    "analysis": ai_resp.data,
                })
            except Exception as e:
                skipped += 1
                errors.append(f"{os.path.basename(path)}: {e}")

        # Write consolidated JSON
        payload = {
            "generated_at": datetime.utcnow().isoformat(),
            "model": "gemini-2.5-flash",
            "home_id": str(home_id),
            "directory": base_dir,
            "total_found": len(files),
            "analyzed": analyzed,
            "skipped": skipped,
            "results": outputs,
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return {
            "output_path": str(out_path),
            "total_found": len(files),
            "analyzed": analyzed,
            "skipped": skipped,
            "errors": errors,
        }

    async def ingest_room_image_analysis_from_json(
        self,
        db: AsyncSession,
        home_id: uuid.UUID,
        json_path: str,
        create_room_images: bool = True,
    ) -> Dict[str, Any]:
        """Ingest previously generated room image analyses from a JSON file into the database.

        The JSON must follow the structure produced by analyze_room_images_to_json.
        Only records with a mapped_room are ingested.
        """
        p = Path(json_path)
        if not p.exists():
            return {"ingested": 0, "skipped": 0, "errors": [f"JSON not found: {json_path}"]}

        with open(p, "r", encoding="utf-8") as f:
            doc = json.load(f)

        if str(doc.get("home_id")) != str(home_id):
            return {"ingested": 0, "skipped": 0, "errors": ["home_id mismatch in JSON"]}

        results = doc.get("results", [])
        ingested = 0
        skipped = 0
        errors: list[str] = []

        for item in results:
            try:
                mapped = item.get("mapped_room")
                if not mapped or not mapped.get("id"):
                    skipped += 1
                    continue

                room_id = uuid.UUID(mapped["id"])
                analysis_data = item.get("analysis") or {}

                # Optionally verify room belongs to home
                result = await db.execute(select(Room).where(Room.id == room_id, Room.home_id == home_id))
                room = result.scalar_one_or_none()
                if not room:
                    skipped += 1
                    continue

                # Create RoomImage (if requested) and related analysis + entities, mirroring analyze_and_save_room_image
                room_image_id = None
                if create_room_images:
                    room_image = RoomImage(
                        room_id=room_id,
                        image_url=item.get("image_path"),
                        image_type="original",
                        view_angle=None,
                        is_analyzed=True,
                        analysis_metadata=analysis_data.get("raw_response", {}),
                    )
                    db.add(room_image)
                    await db.flush()
                    room_image_id = room_image.id

                    img_analysis = ImageAnalysis(
                        room_image_id=room_image_id,
                        description=f"{analysis_data.get('room_style', 'unknown')} {analysis_data.get('room_type', 'room')}",
                        keywords=analysis_data.get("keywords", []),
                        dominant_colors=analysis_data.get("visual_characteristics", {}).get("dominant_colors", []),
                        objects_detected=analysis_data.get("detected_products", []),
                        materials_visible=analysis_data.get("detected_materials", []),
                        fixtures_visible=analysis_data.get("detected_fixtures", []),
                        image_quality_score=0.8,
                        lighting_quality=analysis_data.get("visual_characteristics", {}).get("lighting_quality", "good"),
                        clarity="sharp",
                        view_angle="front",
                        estimated_coverage=0.8,
                        confidence_score=analysis_data.get("confidence_score", 0.0),
                        analysis_model=analysis_data.get("metadata", {}).get("model_used", "gemini-2.5-flash"),
                        analysis_notes=analysis_data.get("analysis_notes", ""),
                    )
                    db.add(img_analysis)

                # Create Materials
                for mat_data in (analysis_data.get("detected_materials", []) or []):
                    material = Material(
                        room_id=room_id,
                        category=mat_data.get("category", "other"),
                        material_type=mat_data.get("material_type", "unknown"),
                        brand=mat_data.get("brand_detected"),
                        color=mat_data.get("color"),
                        finish=mat_data.get("finish"),
                        condition=mat_data.get("condition", "unknown"),
                        extra_data={
                            "detected_from_image": str(room_image_id) if room_image_id else None,
                            "confidence": mat_data.get("confidence", 0.0),
                            "coverage_area": mat_data.get("coverage_area"),
                        },
                    )
                    db.add(material)

                # Create Fixtures
                for fix_data in (analysis_data.get("detected_fixtures", []) or []):
                    fixture = Fixture(
                        room_id=room_id,
                        fixture_type=fix_data.get("fixture_type", "unknown"),
                        brand=fix_data.get("brand_detected"),
                        model=fix_data.get("model_detected"),
                        style=fix_data.get("style"),
                        finish=fix_data.get("finish"),
                        location=fix_data.get("location"),
                        condition=fix_data.get("condition", "unknown"),
                        extra_data={
                            "detected_from_image": str(room_image_id) if room_image_id else None,
                            "confidence": fix_data.get("confidence", 0.0),
                        },
                    )
                    db.add(fixture)

                # Create Products
                for prod_data in (analysis_data.get("detected_products", []) or []):
                    product = Product(
                        room_id=room_id,
                        product_category=prod_data.get("product_category", "unknown"),
                        product_type=prod_data.get("product_type", "unknown"),
                        brand=prod_data.get("brand_detected"),
                        style=prod_data.get("style"),
                        color=prod_data.get("color"),
                        material=prod_data.get("material"),
                        dimensions=prod_data.get("estimated_dimensions", {}),
                        confidence_score=prod_data.get("confidence", 0.0),
                        condition=prod_data.get("condition", "unknown"),
                        extra_data={
                            "detected_from_image": str(room_image_id) if room_image_id else None,
                        },
                    )
                    db.add(product)

                ingested += 1
            except Exception as e:
                errors.append(str(e))
                skipped += 1

        await db.commit()

        return {"ingested": ingested, "skipped": skipped, "errors": errors}

    async def get_home_digital_twin(
        self,
        db: AsyncSession,
        home_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Retrieve complete digital twin data for a home.

        Args:
            db: Database session
            home_id: UUID of the home

        Returns:
            Complete digital twin data structure
        """
        try:
            # Sanitize any invalid room_type values from prior runs to avoid Enum conversion errors
            await self._sanitize_room_types(db, home_id)
            # Load home with all relationships
            result = await db.execute(
                select(Home)
                .options(
                    selectinload(Home.rooms).selectinload(Room.images).selectinload(RoomImage.analyses),
                    selectinload(Home.rooms).selectinload(Room.materials),
                    selectinload(Home.rooms).selectinload(Room.fixtures),
                    selectinload(Home.rooms).selectinload(Room.products),
                    selectinload(Home.rooms).selectinload(Room.spatial_data),
                    selectinload(Home.rooms).selectinload(Room.analyses),
                    selectinload(Home.floor_plans).selectinload(FloorPlan.analyses)
                )
                .where(Home.id == home_id)
            )
            home = result.scalar_one_or_none()

            if not home:
                raise Exception(f"Home {home_id} not found")

            # Build digital twin structure
            digital_twin = {
                "home_id": str(home.id),
                "address": home.address,
                "home_type": home.home_type.value if hasattr(home.home_type, 'value') else str(home.home_type),
                "basic_info": {
                    "name": home.name,
                    "year_built": home.year_built,
                    "square_footage": home.square_footage,
                    "num_bedrooms": home.num_bedrooms,
                    "num_bathrooms": home.num_bathrooms,
                    "num_floors": home.num_floors
                },
                "digital_twin_completeness": home.digital_twin_completeness,
                "floor_plans": [
                    {
                        "id": str(fp.id),
                        "name": fp.name,
                        "floor_level": fp.floor_level,
                        "image_url": fp.image_url,
                        "is_analyzed": fp.is_analyzed
                    }
                    for fp in home.floor_plans
                ],
                "rooms": [
                    {
                        "id": str(room.id),
                        "name": room.name,
                        "room_type": room.room_type.value if hasattr(room.room_type, 'value') else str(room.room_type),
                        "floor_level": room.floor_level,
                        "dimensions": {
                            "length": room.length,
                            "width": room.width,
                            "height": room.height,
                            "area": room.area
                        },
                        "materials": [
                            {
                                "id": str(mat.id),
                                "material_type": mat.material_type,
                                "category": mat.category.value if hasattr(mat.category, 'value') else str(mat.category),
                                "brand": mat.brand,
                                "color": mat.color,
                                "finish": mat.finish,
                                "condition": mat.condition,
                                "age_years": mat.age_years
                            }
                            for mat in room.materials
                        ],
                        "fixtures": [
                            {
                                "id": str(fix.id),
                                "fixture_type": fix.fixture_type,
                                "brand": fix.brand,
                                "model": fix.model,
                                "style": fix.style,
                                "finish": fix.finish,
                                "location": fix.location,
                                "condition": fix.condition,
                                "installation_date": fix.installation_date
                            }
                            for fix in room.fixtures
                        ],
                        "images": [
                            {
                                "id": str(img.id),
                                "image_url": img.image_url,
                                "is_analyzed": img.is_analyzed
                            }
                            for img in room.images
                        ],
                        "images_count": len(room.images),
                        "materials_count": len(room.materials),
                        "fixtures_count": len(room.fixtures),
                        "products_count": len(room.products)
                    }
                    for room in home.rooms
                ],
                "total_rooms": len(home.rooms),
                "total_images": sum(len(room.images) for room in home.rooms)
            }

            return digital_twin

        except Exception as e:
            logger.error(f"Error in get_home_digital_twin: {str(e)}", exc_info=True)
            raise

    async def _sanitize_room_types(self, db: AsyncSession, home_id: uuid.UUID) -> None:
        """Ensure all rooms for the given home have valid enum values for room_type.

        Some earlier analyses may have inserted raw strings not present in the RoomType enum
        (e.g., 'flex_room'). This method coerces any invalid values to 'other' to prevent
        Enum casting errors when loading with SQLAlchemy.
        """
        try:
            # Build a set of valid values from the RoomType enum
            from backend.models.home import RoomType
            valid_values = tuple(rt.value for rt in RoomType)

            # SQLite-compatible UPDATE using NOT IN clause; fall back safely if tuple has 1
            placeholders = ", ".join([f":v{i}" for i in range(len(valid_values))])
            sql = text(
                f"""
                UPDATE rooms
                SET room_type = :other
                WHERE home_id = :home_id
                  AND (room_type IS NULL OR room_type NOT IN ({placeholders}))
                """
            )
            params = {"home_id": str(home_id), "other": "other"}
            for i, val in enumerate(valid_values):
                params[f"v{i}"] = val
            await db.execute(sql, params)
            await db.commit()
        except Exception as e:
            logger.warning(f"Room type sanitation skipped/failed: {e}")

    async def ingest_image_links_and_analyses(
        self,
        db: AsyncSession,
        home_id: uuid.UUID,
        links_path: str,
        analyses_path: str,
        rename_files: bool = False,
        rename_template: str = "{home}-{floor}-{roomtype}-{roomname}-{index}{ext}",
        score_threshold: float = 1.5,
    ) -> Dict[str, Any]:
        """
        Ingest image-to-room links and DB-aligned analyses previously generated (e.g., by notebook),
        without re-running any AI. Idempotent by (image_url) uniqueness.

        links_path: JSON from image_room_links_v2.json with fields { filename, candidates: [ { room_id, score, breakdown } ] }
        analyses_path: JSON from image_analyses_db_aligned.json with fields { filename, image_analysis, room_analysis, extras }

        If rename_files=True, attempt to rename image files on disk to a canonical name and store the new path.
        """
        from sqlalchemy import select
        from pathlib import Path
        import os
        import json as _json

        # Normalize home_id to UUID
        try:
            if not isinstance(home_id, uuid.UUID):
                home_id = uuid.UUID(str(home_id))
        except Exception:
            raise ValueError("home_id must be a valid UUID")

        # Load and index inputs
        lp = Path(links_path)
        ap = Path(analyses_path)
        if not lp.exists() or not ap.exists():
            return {"ingested": 0, "skipped": 0, "errors": [f"Missing files: links={links_path}, analyses={analyses_path}"]}

        with open(lp, "r", encoding="utf-8") as f:
            links = _json.load(f)
        with open(ap, "r", encoding="utf-8") as f:
            analyses = _json.load(f)

        # Build maps by filename
        by_filename_links = { (rec.get("filename") or rec.get("image")): rec for rec in links }
        by_filename_analysis = { (rec.get("filename") or rec.get("image")): rec for rec in analyses }

        # Helper: slugify for filenames
        def slug(s: str) -> str:
            import re
            s = (s or "").strip().lower()
            s = re.sub(r"[^a-z0-9]+", "-", s)
            return s.strip("-")

        async def _room_exists(room_id: uuid.UUID) -> bool:
            res = await db.execute(select(Room).where(Room.id == room_id, Room.home_id == home_id))
            return res.scalar_one_or_none() is not None

        async def _roomimage_exists(path: str) -> bool:
            res = await db.execute(select(RoomImage).where(RoomImage.image_url == path))
            return res.scalar_one_or_none() is not None

        async def _get_room(room_id: uuid.UUID) -> Optional[Room]:
            res = await db.execute(select(Room).where(Room.id == room_id, Room.home_id == home_id))
            return res.scalar_one_or_none()

        ingested = 0
        skipped = 0
        errors: list[str] = []

        # Iterate through links; for each filename, find its analysis, pick top candidate, and persist
        for fname, link in by_filename_links.items():
            try:
                candidates = link.get("candidates") or []
                if not candidates:
                    skipped += 1
                    continue

                top = candidates[0]
                if top.get("score", 0) < score_threshold:
                    # Low confidence, skip for manual review
                    skipped += 1
                    continue

                rid_str = top.get("room_id")
                if not rid_str:
                    skipped += 1
                    continue

                # Accept UUIDs; otherwise, try to resolve by name/floor/type from candidate payload
                try:
                    rid = uuid.UUID(rid_str)
                    if not await _room_exists(rid):
                        skipped += 1
                        continue
                except Exception:
                    # Fallback: resolve by (room_name, floor_number[, room_type])
                    try:
                        cand_name = (top.get("room_name") or "").strip()
                        cand_floor = top.get("floor_number")
                        cand_type = (top.get("room_type") or "").strip().lower()

                        query = select(Room).where(Room.home_id == home_id)
                        if cand_name:
                            # Case-insensitive compare
                            query = query.where(Room.name.ilike(cand_name))
                        if cand_floor is not None:
                            query = query.where(Room.floor_level == cand_floor)

                        # Try narrowing by room_type if provided
                        try:
                            from backend.models.home import RoomType as _RT
                            if cand_type:
                                # Some variants like "master_bedroom" or "living_room" are supported
                                query = query.where(Room.room_type == _RT(cand_type))
                        except Exception:
                            pass

                        res = await db.execute(query)
                        room_match = res.scalar_one_or_none()
                        if room_match is None:
                            skipped += 1
                            continue
                        rid = room_match.id
                    except Exception:
                        skipped += 1
                        continue

                arec = by_filename_analysis.get(fname)
                if not arec:
                    # Try matching by image path end
                    arec = next((v for k, v in by_filename_analysis.items() if k and k.lower() == fname.lower()), None)
                if not arec:
                    skipped += 1
                    continue

                # Original image path (from analyses) or compose from links
                img_path = arec.get("image") or link.get("image")
                if not img_path:
                    skipped += 1
                    continue

                # Compute final storage path (optionally rename)
                final_path = img_path
                if rename_files:
                    room = await _get_room(rid)
                    if room:
                        ext = os.path.splitext(img_path)[1] or ".jpg"
                        new_name = rename_template.format(
                            home=str(home_id)[:8],
                            floor=str(room.floor_level),
                            roomtype=slug(getattr(room.room_type, 'value', str(room.room_type))),
                            roomname=slug(room.name),
                            index=str(ingested + skipped + 1),
                            ext=ext,
                        )
                        # Place next to original
                        src = Path(img_path)
                        dst = src.with_name(new_name)
                        try:
                            if src.exists() and str(src).lower() != str(dst).lower():
                                src.rename(dst)
                            final_path = str(dst)
                        except Exception as re:
                            # On Windows, rename may fail if open; fallback to original name
                            final_path = img_path

                # Idempotency: skip if RoomImage with this path already exists
                if await _roomimage_exists(final_path):
                    skipped += 1
                    continue

                # Create RoomImage
                room_image = RoomImage(
                    room_id=rid,
                    image_url=final_path,
                    image_type="original",
                    view_angle=arec.get("image_analysis", {}).get("view_angle"),
                    is_analyzed=True,
                    analysis_metadata={
                        "source": "notebook-db-aligned",
                        "links_breakdown": top.get("breakdown", {}),
                    },
                )
                db.add(room_image)
                await db.flush()

                ia = arec.get("image_analysis", {})

                # Create ImageAnalysis row
                img_analysis = ImageAnalysis(
                    room_image_id=room_image.id,
                    description=ia.get("description"),
                    keywords=ia.get("keywords") or [],
                    dominant_colors=ia.get("dominant_colors") or [],
                    objects_detected=ia.get("objects_detected") or [],
                    materials_visible=ia.get("materials_visible") or [],
                    fixtures_visible=ia.get("fixtures_visible") or [],
                    image_quality_score=ia.get("image_quality_score"),
                    lighting_quality=ia.get("lighting_quality"),
                    clarity=ia.get("clarity"),
                    view_angle=ia.get("view_angle"),
                    estimated_coverage=ia.get("estimated_coverage"),
                    confidence_score=ia.get("confidence_score"),
                    analysis_model=ia.get("analysis_model", "gemini-2.5-flash"),
                    analysis_notes=(arec.get("room_analysis", {}) or {}).get("analysis_notes") or "",
                )
                db.add(img_analysis)

                # Optionally: persist products/materials/fixtures as entities later

                ingested += 1
            except Exception as e:
                errors.append(f"{fname}: {e}")
                await db.rollback()
            else:
                # Commit per item to maximize resilience
                await db.commit()

        return {"ingested": ingested, "skipped": skipped, "errors": errors}

    async def ingest_links_and_analyses_objects(
        self,
        db: AsyncSession,
        home_id: uuid.UUID,
        links: List[Dict[str, Any]],
        analyses: List[Dict[str, Any]],
        rename_files: bool = False,
        rename_template: str = "{home}-{floor}-{roomtype}-{roomname}-{index}{ext}",
        score_threshold: float = 1.5,
    ) -> Dict[str, Any]:
        """
        Ingest image-to-room links and DB-aligned analyses provided as in-memory objects.

        links: list of { filename|image, candidates: [ { room_id|room_name|floor_number|room_type, score, breakdown } ] }
        analyses: list of { filename|image, image_analysis: {...}, room_analysis: {...}, extras: {...} }
        """
        from sqlalchemy import select
        from pathlib import Path
        import os

        # Normalize home_id to UUID
        try:
            if not isinstance(home_id, uuid.UUID):
                home_id = uuid.UUID(str(home_id))
        except Exception:
            raise ValueError("home_id must be a valid UUID")

        # Build maps by filename
        by_filename_links = { (rec.get("filename") or rec.get("image")): rec for rec in (links or []) }
        by_filename_analysis = { (rec.get("filename") or rec.get("image")): rec for rec in (analyses or []) }

        # Helper: slugify for filenames
        def slug(s: str) -> str:
            import re
            s = (s or "").strip().lower()
            s = re.sub(r"[^a-z0-9]+", "-", s)
            return s.strip("-")

        async def _room_exists(room_id: uuid.UUID) -> bool:
            res = await db.execute(select(Room).where(Room.id == room_id, Room.home_id == home_id))
            return res.scalar_one_or_none() is not None

        async def _roomimage_exists(path: str) -> bool:
            res = await db.execute(select(RoomImage).where(RoomImage.image_url == path))
            return res.scalar_one_or_none() is not None

        async def _get_room(room_id: uuid.UUID) -> Optional[Room]:
            res = await db.execute(select(Room).where(Room.id == room_id, Room.home_id == home_id))
            return res.scalar_one_or_none()

        ingested = 0
        skipped = 0
        errors: list[str] = []

        for fname, link in by_filename_links.items():
            try:
                candidates = link.get("candidates") or []
                if not candidates:
                    skipped += 1
                    continue

                top = candidates[0]
                if top.get("score", 0) < score_threshold:
                    skipped += 1
                    continue

                rid_str = top.get("room_id")
                if not rid_str:
                    skipped += 1
                    continue

                # Accept UUIDs; otherwise, try to resolve by name/floor/type from candidate payload
                try:
                    rid = uuid.UUID(rid_str)
                    if not await _room_exists(rid):
                        skipped += 1
                        continue
                except Exception:
                    try:
                        cand_name = (top.get("room_name") or "").strip()
                        cand_floor = top.get("floor_number")
                        cand_type = (top.get("room_type") or "").strip().lower()

                        query = select(Room).where(Room.home_id == home_id)
                        if cand_name:
                            query = query.where(Room.name.ilike(cand_name))
                        if cand_floor is not None:
                            query = query.where(Room.floor_level == cand_floor)

                        try:
                            from backend.models.home import RoomType as _RT
                            if cand_type:
                                query = query.where(Room.room_type == _RT(cand_type))
                        except Exception:
                            pass

                        res = await db.execute(query)
                        room_match = res.scalar_one_or_none()
                        if room_match is None:
                            skipped += 1
                            continue
                        rid = room_match.id
                    except Exception:
                        skipped += 1
                        continue

                arec = by_filename_analysis.get(fname)
                if not arec:
                    # Try matching by image path end
                    arec = next((v for k, v in by_filename_analysis.items() if k and k.lower() == (fname or '').lower()), None)
                if not arec:
                    skipped += 1
                    continue

                img_path = arec.get("image") or link.get("image") or arec.get("filename")
                if not img_path:
                    skipped += 1
                    continue

                final_path = img_path
                if rename_files:
                    room = await _get_room(rid)
                    if room:
                        ext = os.path.splitext(img_path)[1] or ".jpg"
                        new_name = rename_template.format(
                            home=str(home_id)[:8],
                            floor=str(room.floor_level),
                            roomtype=slug(getattr(room.room_type, 'value', str(room.room_type))),
                            roomname=slug(room.name),
                            index=str(ingested + skipped + 1),
                            ext=ext,
                        )
                        src = Path(img_path)
                        dst = src.with_name(new_name)
                        try:
                            if src.exists() and str(src).lower() != str(dst).lower():
                                src.rename(dst)
                            final_path = str(dst)
                        except Exception:
                            final_path = img_path

                if await _roomimage_exists(final_path):
                    skipped += 1
                    continue

                room_image = RoomImage(
                    room_id=rid,
                    image_url=final_path,
                    image_type="original",
                    view_angle=(arec.get("image_analysis", {}) or {}).get("view_angle"),
                    is_analyzed=True,
                    analysis_metadata={
                        "source": "ui-bulk-upload",
                        "links_breakdown": top.get("breakdown", {}),
                    },
                )
                db.add(room_image)
                await db.flush()

                ia = (arec.get("image_analysis", {}) or {})

                img_analysis = ImageAnalysis(
                    room_image_id=room_image.id,
                    description=ia.get("description"),
                    keywords=ia.get("keywords") or [],
                    dominant_colors=ia.get("dominant_colors") or [],
                    objects_detected=ia.get("objects_detected") or [],
                    materials_visible=ia.get("materials_visible") or [],
                    fixtures_visible=ia.get("fixtures_visible") or [],
                    image_quality_score=ia.get("image_quality_score"),
                    lighting_quality=ia.get("lighting_quality"),
                    clarity=ia.get("clarity"),
                    view_angle=ia.get("view_angle"),
                    estimated_coverage=ia.get("estimated_coverage"),
                    confidence_score=ia.get("confidence_score"),
                    analysis_model=ia.get("analysis_model", "gemini-2.5-flash"),
                    analysis_notes=(arec.get("room_analysis", {}) or {}).get("analysis_notes") or "",
                )
                db.add(img_analysis)

                ingested += 1
            except Exception as e:
                errors.append(f"{fname}: {e}")
                await db.rollback()
            else:
                await db.commit()

        return {"ingested": ingested, "skipped": skipped, "errors": errors}

