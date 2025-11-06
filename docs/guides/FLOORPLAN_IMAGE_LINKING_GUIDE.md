# Floor Plan ↔ Interior Image Linking Guide (Gemini 2.5 Flash/Pro)

This guide describes how to build an end-to-end pipeline that: (1) parses architectural floor plans into structured geometry and dimensions, (2) analyzes interior photos of the same home, and (3) links images to rooms and floor plan coordinates so you get a complete, queryable picture for home improvement workflows.

The notebook `notebooks/05_multi_floor_plan_detection.ipynb` already extracts multi-floor geometry and room dimensions using a 3ST-driven prompt. Here we extend it with image tagging and robust linking.

---

## Goals

- Produce a single, consistent data graph per home: floors → rooms → walls/doors/windows, with units and pixel-to-unit scale.
- Tag each interior photo with: room type, features (fixtures/furniture/materials), view angle, and estimated camera location + viewing direction on the floor plan.
- Support multiple angles per room; cluster and rank images for coverage (e.g., 4 cardinal views per room).
- Make results explorable in UI: overlay camera icons on the plan; clicking cycles images for that room.

---

## Unified Data Schema

Use the floor-plan JSON output (schema_version "2.0") from the notebook as the authoritative geometry. Add two additional entity types for photos and links.

- Home
  - id, address, metadata

- Floor (from plan JSON `floors[]`)
  - id, floor_number, floor_type, section_bbox, pixel_to_unit, detection_confidence

- Room (from plan JSON `floors[].rooms[]`)
  - id (stable_id), room_type, name, polygon (list of [x,y] in image pixels), centroid, measured_dimensions (length/width/perimeter/area with unit and source), confidence

- Photo (new)
  - id, file_path, width_px, height_px, exif (make, model, focal_len, timestamp),
  - image_tags: ["window", "sink", "island", "sofa", ...]
  - predicted_room_type, scene_type (kitchen/bath/bed/etc.), materials (flooring, wall paint color),
  - view_category (corner|center|diagonal|hallway), view_dir_deg (0–359, clockwise, image up is 0), hfov_deg (if derivable),
  - quality: sharpness, blur, dynamic_range, lighting, confidence

- RoomPhotoLink (new)
  - id, home_id, floor_id, room_id, photo_id
  - confidence (0–1)
  - match_features: { window_count, door_count, furniture_overlap, room_type_match, area_tolerance, notes }
  - camera_pose: { x: float, y: float, floor_coords: "image_pixel", view_dir_deg: float, pose_confidence: float }
  - coverage_label: "north wall", "south corner", etc. (optional)

Store this in Postgres or SQLite (for prototyping). A simple table layout:

- homes(id, address, created_at)
- floors(id, home_id, number, type, section_bbox_json, pixel_to_unit_json, confidence)
- rooms(id, floor_id, stable_id, type, name, polygon_json, centroid_json, dimensions_json, confidence)
- photos(id, home_id, file_path, width_px, height_px, exif_json, tags_json, predicted_room_type, materials_json, view_category, view_dir_deg, hfov_deg, quality_json, confidence)
- room_photo_links(id, home_id, floor_id, room_id, photo_id, confidence, match_features_json, camera_pose_json, coverage_label)

---

## End-to-End Pipeline

1) Floor Plan Extraction (done in the provided notebook)
- Input: a floor plan image (single or multi-floor in one sheet)
- Output: `schema_version=2.0` JSON with floors, rooms (polygons), walls/doors/windows, units, pixel_to_unit, adjacency, and quality checks.
- Save to `uploads/floor_plans/analysis/*.json`.

2) Interior Photo Analysis (Gemini 2.5 Flash Image)
- For each JPEG/PNG in your photo set for the home, call Gemini 2.5 Flash Image with a structured prompt (example below).
- Output: JSON per photo with: predicted_room_type, features (fixtures/furniture/materials), counts (window/door/fixtures), view_category, estimated view_dir_deg, quality, and any text/OCR notes.
- Save to `uploads/room_images/analysis/*.json`.

3) Candidate Room Matching
- For each photo, compute candidate rooms:
  - Filter rooms by predicted_room_type.
  - If none, fall back to all rooms with a type prior (e.g., bathrooms < bedrooms < living).
- Score each candidate using:
  - Room-type match: exact=1.0, related=0.6 (e.g., great_room vs living_room)
  - Fixture/furniture overlap (set Jaccard across tags: sink, tub, island, bed, sofa, fireplace)
  - Window/door count similarity (penalty if big mismatch)
  - Area tolerance: |photo-inferred-room-size − plan area| / plan area (penalize large gaps, if image can estimate size via objects)
  - Adjacency plausibility: if photo shows an opening to a room of type T, boost candidates adjacent to rooms of type T.
- Pick top-1 if score gap > threshold; otherwise keep top-3 for manual confirmation.

4) Camera Pose Estimation (optional but valuable)
- Use layout cues and vanishing points to infer the camera facing direction.
- Align visible walls to the room polygon to estimate (x,y) as the approximate camera location and `view_dir_deg`.
- If windows are visible, match their count/relative spacing to the corresponding wall in the polygon.
- Store pose with `pose_confidence` based on match consistency.

5) Persist and Index
- Insert photo rows; insert RoomPhotoLink rows with confidence and match_features.
- Generate embeddings (optional) for photos using a vision embedding model to cluster near-duplicates and group angles per room.

6) UI Overlay (suggested)
- Draw camera icons in the room polygon at `camera_pose (x,y)`; rotate arrow by `view_dir_deg`.
- Clicking a camera icon opens the photo. Provide a room gallery that orders photos by coverage (N/E/S/W or corner vs center).

7) Review Loop (human-in-the-loop)
- If link confidence < 0.6 or multiple close candidates, queue for review.
- Provide controls to reassign photo to a room and adjust camera pose; write back corrections.

---

## Gemini 2.5 Flash Image Prompt (Photo Tagging)

Use this prompt for each interior photo. Return only JSON as shown.

```
You are an expert interior photo analyst. Analyze the provided interior image and return only valid JSON per the schema below.

Tasks:
- Predict room_type (kitchen, bathroom, bedroom, living_room, dining_room, hallway, laundry, office, garage, basement_room, utility, closet, entry, stair).
- Extract features
  - fixtures/furniture: bed, sofa, table, chairs, kitchen_island, sink(single/double), stove, oven, microwave, fridge, dishwasher, toilet, tub, shower, vanity, washer, dryer, fireplace, TV, shelving, wardrobe.
  - counts: window_count, door_count (visible), plumbing_fixtures_count.
  - materials/colors (optional): flooring (hardwood/tile/carpet, color), wall color (approximate), countertop type (stone/laminate), cabinet color.
- View meta
  - view_category: corner|center|diagonal|hallway|unknown
  - estimate view_dir_deg: 0–359 degrees, where 0 means the top of image is forward. If unknown, return null.
  - hfov_deg: if inferable; else null.
- Quality meta
  - lighting, blur/sharpness, dynamic_range, overall confidence.

Output JSON schema:
{
  "schema_version": "img-1.0",
  "photo": {
    "predicted_room_type": "kitchen|bathroom|bedroom|living_room|...",
    "features": ["sink","shower","island","sofa", ...],
    "counts": { "window": <int>, "door": <int>, "plumbing_fixtures": <int> },
    "materials": { "flooring": "tile|hardwood|carpet|...", "wall_color": "light gray" , "countertop": "stone|laminate|..." },
    "view": { "view_category": "corner|center|diagonal|hallway|unknown", "view_dir_deg": <int|null>, "hfov_deg": <int|null> },
    "quality": { "lighting": "good|dim|mixed", "sharpness": "sharp|soft|blurry", "dynamic_range": "ok|clipped", "confidence": <0.0-1.0> }
  }
}

CRITICAL:
- Return only JSON that matches the schema. No markdown or extra text.
```

---

## Linking Algorithm (Scoring)

For a photo P and a candidate room R:

```
score(P,R) =
  + 0.45 * room_type_match(P,R)
  + 0.25 * jaccard(features(P), features(R_expected))   # kitchen: sink, island; bath: tub/shower/vanity; etc.
  + 0.10 * similarity(counts(P).windows, counts(R).windows_est)
  + 0.10 * similarity(counts(P).doors, counts(R).doors_est)
  + 0.05 * adjacency_bonus(P,R)                         # opening to likely neighbor
  + 0.05 * area_consistency(P_est_area, plan_area(R))   # optional, if image-derived
  - 0.10 * pose_inconsistency_penalty(P_pose, R_polygon) # optional, if pose estimated

where similarity(a,b) = 1 - min(1, |a-b|/max(1,b)) and room_type_match ∈ {1.0 exact, 0.6 related, 0.2 unknown}.
```

Thresholds
- If top-1 − top-2 ≥ 0.15, accept top-1 automatically; else queue for review with top-3 candidates.

---

## Evaluation & QA

Track these metrics over a validation set:
- Linking precision@1 and precision@3
- Coverage: fraction of photos linked with confidence ≥ 0.6
- Room clustering purity (photos grouped per room id)
- Pose plausibility: fraction of poses consistent with room polygon and window/door layout

Use a small manual review UI to correct mislinks. Feed corrections back as training signals or heuristics.

---

## Storage Patterns

- Prefer stable IDs in plan output (`rooms[].id`).
- Keep original image coordinates for polygons; store `section_bbox` to clip to floor area and compute normalized coordinates if needed.
- For multi-floor sheets, store `floor_id` in links to avoid cross-floor mixups.
- Use `camera_pose.floor_coords = "image_pixel"` (the plan image coordinate system). If you vectorize to CAD/IFC later, keep a transform record.

---

## Practical Runbook

1) Run `05_multi_floor_plan_detection.ipynb` to produce the plan JSON (Flash or Pro).
2) Batch-run photo tagging with Gemini 2.5 Flash Image; save each JSON under `uploads/room_images/analysis`.
3) Run a linker script/notebook to create `room_photo_links` using scoring above; write to DB/JSON.
4) Render a simple viewer:
   - Show the plan; draw room polygons; draw camera icons with direction.
   - Click camera icons to open images; provide reassignment controls.

---

## Notes & Tips

- Use the Pro model for floor plan parsing if accuracy on polygons or text OCR is critical; Flash is faster for bulk photo tagging.
- Normalize names (e.g., KIT, KITCHEN → kitchen) with the same mapping on both sides.
- De-duplicate near-identical photos via perceptual hash or vision embeddings before linking.
- Keep a fallback: if no strong match, assign to the closest room type by area and adjacency, but mark `confidence < 0.5` for review.

---

## Artifacts

- Plan JSON: `uploads/floor_plans/analysis/<stem>_analysis_<model>_<ts>.json`
- Photo JSON: `uploads/room_images/analysis/<photo_stem>_analysis_<ts>.json`
- Links in DB or `uploads/room_images/analysis/<stem>_links_<ts>.json`

This guide is implementation-ready with your current notebook and can be expanded into an API (FastAPI in `backend/`) once the linking prototype is validated.
