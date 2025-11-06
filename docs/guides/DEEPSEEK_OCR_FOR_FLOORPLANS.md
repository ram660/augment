# Using DeepSeek-OCR to Boost Floor Plan Accuracy

This guide explains how DeepSeek-OCR (Contexts Optical Compression) can improve your floor plan parsing and photo–room linking accuracy. It translates the paper’s key ideas into actionable integration points for your current workflow that uses Gemini 2.5 Flash/Pro for analysis and JSON extraction.

## Why DeepSeek-OCR helps here

DeepSeek-OCR shows competitive OCR quality at very low vision-token budgets and supports high-resolution inputs with dynamic tiling (Gundam modes). For floor plans, this translates into:

- Stronger text/OCR precision for faint or dense annotations (dimensions, room labels, scale notes), especially on big sheets.
- Robust performance on very large or multi-panel plan sheets without exhausting memory.
- Practical throughput: can handle large volumes if you later scale to batch digitization.

These strengths address the accuracy bottlenecks in your pipeline: unit/scale detection, room naming normalization, dimension OCR vs. estimated dimensions, adjacency inferred from door/window labels, and stair continuity notes.

## Where to integrate DeepSeek-OCR in your pipeline

- OCR subsystem for text extraction:
  - Use DeepSeek-OCR as a specialized OCR pass focused on: room labels, dimension strings (L×W), scale references, notes/legends, stair up/down arrows or labels, and window/door annotations.
  - Feed its outputs into your existing JSON schema (`floors[].texts[]`, `rooms[].label_ocr`, and dimension parsing in `rooms[].measured_dimensions`).

- Scale and units resolution:
  - Extract “Scale 1/4"=1'-0"” or “1:100” reliably from title blocks/legends using DeepSeek-OCR.
  - Improve pixel_to_unit inference confidence and reduce the number of rooms with estimated dimensions.

- Room label normalization:
  - Use OCR’d raw labels as evidence to normalize to your canonical room types (KIT→kitchen, LIV→living_room, WIC→closet, etc.).
  - Boost room-type confidence and reduce misclassifications that drift polygon labeling.

- Dimension precedence policy:
  - Elevate OCR-based dimensions to the top of your dimension precedence (ocr > scale > estimate) with stronger trust when DeepSeek-OCR confidence is high.

- Door/Window/stairs metadata:
  - Use OCR to read notes like “SLIDING DOOR”, “CASEMENT”, “UP” next to stair arrows. This helps adjacency, window types, and stair direction consistency.

## Hybrid inference pattern (Gemini + DeepSeek-OCR)

1) Geometry-first with Gemini (current notebook)
- Continue using Gemini 2.5 Flash/Pro to detect sections, polygons, adjacency, and an initial pass at texts.

2) OCR refinement with DeepSeek-OCR
- Run DeepSeek-OCR on the same floor plan image (or per-floor cropped section_bbox) targeting text precision.
- Prefer Gundam/Base modes for large, detailed sheets (higher token budgets for complex plans) and Tiny/Small for simple sheets.

3) Merge results
- Replace or augment `floors[].texts[]` with higher-precision OCR.
- Promote OCR-derived `units.scale_text`, resolve `pixel_to_unit` sources.
- Recompute `rooms[].measured_dimensions` precedence; mark fewer as `estimated=true`.
- Add structured notes (e.g., window types) from OCR to enrich `windows[]` and `doors[]`.

4) Validate and re-score
- Your compare cell (Flash vs Pro) can be extended to score the merged result versus Gemini-only using:
  - More rooms with OCR-derived dimensions
  - Lower area-consistency error
  - Fewer warnings/errors tied to scale uncertainty or missing labels
  - Increased adjacency plausibility (from labeled openings/stairs)

## Implementation blueprint

- Extraction contracts
  - Input: Plan image (optionally per-floor crops via `section_bbox`).
  - Output: JSON with:
    - texts: [{ text, bbox, category }]
    - scale_text, unit system hints (imperial/metric cues)
    - dimension strings per room if OCR locates them near/inside polygons
    - labeled symbols (UP/DN, window/door type notes)

- Merge logic
  - Scale: If `units.scale_text` from DeepSeek-OCR is high-confidence, set units.system and compute `pixel_to_unit` (per-floor). Record `inferred_from = scale_text`.
  - Dimensions: Parse OCR dimension strings into numeric L/W. If valid and consistent with polygon aspect, set source="ocr"; else keep scale-derived.
  - Labels: Map OCR labels → canonical room_type; store raw label in `label_ocr`.
  - Symbols: Map nearby text tokens (e.g., “UP”, “SLIDING”) to enrich `stairs[]`, `doors[]`, `windows[]`.

- Confidence and QA
  - Save per-token OCR confidence. Only override geometry-derived values when OCR confidence exceeds a threshold (e.g., ≥0.75) or when it resolves prior uncertainty.
  - Log conflicts (e.g., OCR says metric but door heuristic suggests imperial) to `warnings[]`.

## Practical tips from the paper

- Dynamic resolution modes (Gundam/Gundam-M)
  - For large sheets with many labels, run a global view plus a few tiles. This boosts OCR on small text while maintaining context.
  - Cap tiles between 2–9 to avoid over-fragmentation.

- Token compression perspective
  - If you need to pass a lot of textual context downstream (e.g., for agentic suggestions), you can compress older or peripheral notes into rendered images and re-OCR later for retrieval, keeping active token budgets low.

- Throughput
  - If you batch digitize many plans, DeepSeek-OCR offers good throughput; schedule it as an async refinement step after initial Gemini geometry.

## Expected accuracy gains

- Units/scale resolution: Higher success rate at reading scale text → better `pixel_to_unit` → more accurate areas and dimensions.
- Dimensions: More rooms with OCR-derived L/W (fewer estimates), improved area consistency, reduced warnings.
- Room labels: Cleaner normalization → fewer mis-typed rooms and more reliable adjacency.
- Feature types: More precise door/window/stair descriptors for topology and cross-floor consistency.

## Evaluation plan (drop-in to your compare notebook)

- Add an OCR-refined variant
  - For the same plan, produce: Baseline (Gemini-only), OCR-Refined (Gemini + DeepSeek-OCR merge).
- Metrics already present in your compare cell can be reused:
  - ocr_dim_rooms: expect a higher count
  - area_consistency_mean_abs_pct: expect lower error
  - warnings_total/errors_total: expect reductions related to scale/labels
  - adjacency_edges_total: may increase if OCR reveals openings/notes

- Decision rule
  - Prefer OCR-Refined if it improves 2+ of the above metrics with no major regressions; otherwise fall back to Baseline but flag for review.

## Integration sequence

1) Add a small service/module: `ocr/deepseek_ocr_refine.py`
- Input: image path (and per-floor crops), baseline JSON
- Output: merged JSON with updated texts, scale, dimensions, labels, and features

2) Extend the notebook
- New cell to call the OCR refine step and then re-run visualization + scoring against the baseline.

3) Store provenance
- Record `ocr_engine: deepseek-ocr` and mode (Tiny/Small/Base/Large/Gundam) and confidence summaries.

4) Feature-gated rollout
- Enable via env flag `USE_OCR_REFINEMENT=true` and collect metrics before making it default.

## Notes

- Keep Gemini for geometry and reasoning; use DeepSeek-OCR where text fidelity is critical.
- If DeepSeek-OCR is not installed locally, you can stub the interface and switch providers later.
- For multi-floor images, use `section_bbox` crops to focus OCR passes and reduce false matches across floors.
