# HomeVision Studio Notebooks — Complete Prompt Context and Usage Guide

This document summarizes all notebooks in `notebooks/` so you can hand it to another model as a rich context bundle. It captures goals, key functions, prompts, inputs/outputs, metrics, directories, and expected artifacts—without exposing any secrets.

- Workspace: `c:\Users\ramma\ai-studio`
- Notebooks folder: `notebooks/`
- Image IO root (created by notebooks): `homevision_tests/`
  - `input_images/`: provide your room photos (JPG/PNG; ≥1024x1024 recommended)
  - `output_images/`: notebook-specific subfolders (e.g., `paint_tests/`, `flooring_tests/`)
  - `results/`, `metrics/`: metadata and CSVs
- Environment: requires a valid Gemini API key in the environment (see “Prerequisites”)

## Prerequisites

- Python libraries (not exhaustive; each notebook installs/uses what it needs):
  - Core: `google-generativeai`, `pillow`, `python-dotenv`, `matplotlib`, `ipywidgets`
  - Metrics/analysis: `scikit-image`, `opencv-python`, `pandas`, `seaborn`
- Environment variables (do not include actual keys in prompts or docs):
  - `GOOGLE_API_KEY` or `GEMINI_API_KEY` — used to configure the Gemini client
- Models used:
  - Text: `gemini-2.5-flash` (text-only)
  - Image in/out: `gemini-2.5-flash-image` (required for image generation/editing)

Important: To get image outputs, always use `gemini-2.5-flash-image` (several notebooks reinforce this).

## Shared folder layout created by notebooks

- `homevision_tests/`
  - `input_images/` — drop test room photos here
  - `output_images/`
    - `paint_tests/`
    - `flooring_tests/`
    - `furniture_tests/`
    - `lighting_tests/`
    - `color_scheme_tests/`
  - `results/` — JSON metadata for some runs
  - `metrics/` — CSV summaries from quality assessments

## Notebook 1 — Gemini API Setup & Basics (`01_gemini_setup_and_basics.ipynb`)

- Goals: set up API connection, test basic image upload/processing, validate prompt structure, establish baseline metrics.
- Key steps:
  - Installs: `google-generativeai pillow python-dotenv ipywidgets matplotlib`
  - Loads env via `dotenv`; configures API using `GOOGLE_API_KEY` or `GEMINI_API_KEY`.
  - Creates `homevision_tests/{input_images,output_images,results}`.
  - Helper functions:
    - `load_image(path)`: loads and prints basic info
    - `display_images(images, titles, figsize)`: side-by-side display
    - `save_result(image, scenario_name, metadata)`: saves PNG + JSON metadata
  - Baseline tests:
    - Lists images in `input_images/`; displays first image if present
    - Runs descriptive analysis using `gemini-2.5-flash` (text analysis of an image when passed as a part of the content array)
  - Core prompt templates:
    - `CORE_RULES`: photorealism, preserve perspective, no annotations/text, lighting consistency, etc.
    - `LIGHTING_RULES`: maintain light direction, reflections, material realism
- Outputs: Printed status, optional JSON analysis text, no enforced image edits in this notebook.

## Notebook 2 — Paint Color Testing (`02_paint_color_testing.ipynb`)

- Goals: paint color application on walls, validate color accuracy/photorealism, finishes comparison, quality baseline.
- Setup: repo-level env load; `PAINT_DIR = output_images/paint_tests`.
- Data: `PAINT_COLORS` dict covering Sherwin-Williams, Benjamin Moore, Behr with names/codes/descriptions; finishes list.
- Critical model: `gemini-2.5-flash-image` (image input and image output). The notebook explicitly warns that `gemini-2.5-flash` is text-only.
- Function: `apply_paint_color(image, brand, color_name, color_code, finish, room_type, lighting_type, area_coords=None, model_name='gemini-2.5-flash-image')`
  - Prompt enforces: change ALL walls to specified color, preserve all other elements, realistic finish and lighting, image-only response.
  - Response parsing: extracts `inline_data` image; returns success flag, image, and metadata (brand, color, finish, model, processing time).
- Tests:
  - Single color application (e.g., Sherwin-Williams Naval)
  - Multiple dark colors for maximum visual contrast
  - Finishes comparison: Matte, Eggshell, Satin, Semi-Gloss
- Quality checklist (manual, markdown rendered): color accuracy, photorealism, finish accuracy, preservation.
- Outputs: side-by-side plots; saved images and per-run metadata JSONs in `PAINT_DIR`; a summary printout with average processing time.

## Notebook 3 — Quality Metrics & Testing Framework (`03_quality_metrics_testing.ipynb`)

- Goals: automated quality scoring, A/B testing prompts, regression suite, baseline thresholds.
- Installs: `scikit-image opencv-python pandas seaborn` (on top of prior deps).
- Setup: `metrics/` folder under `homevision_tests`.
- Metrics functions:
  - `calculate_preservation_score(orig, mod, preserve_region)`: SSIM over regions that should not change (0–100)
  - `calculate_change_score(orig, mod, change_region)`: mean absolute difference over target region (0–100)
  - `detect_artifacts(image)`: Laplacian variance (sharpness), Canny edge density; flags `is_blurry`, `has_good_detail`
  - `calculate_color_accuracy(mod, target_rgb, sample_region)`: Euclidean RGB distance → 0–100
  - `comprehensive_quality_score(...)`: weighted aggregate with/without color accuracy
- A/B testing support:
  - `PROMPT_VARIANTS` dictionary with different emphasis: preservation, color accuracy, photorealism
- Batch assessment:
  - Loads originals and `paint_tests` results; computes scores; writes CSV summary to `metrics/`
  - Visualizations: histograms, boxplots, difference heatmaps; readiness distribution with thresholds
- Thresholds for readiness (tunable, current defaults):
  - Production ready: Overall ≥85, Preservation ≥90, Artifacts ≥85
  - Acceptable: Overall ≥75, Preservation ≥80, Artifacts ≥75
- Outputs: console tables/plots, CSVs in `metrics/`, markdown testing summary saved with timestamp.

## Notebook 4 — Flooring Replacement (`04_flooring_replacement.ipynb`)

- Goals: replace flooring (harder than paint), apply metrics from Notebook 3, test several materials, preserve walls/furniture.
- Data: `FLOORING_OPTIONS` dict (oak/walnut hardwood, marble/slate tile, gray LVP, beige carpet) with material/color/pattern descriptors.
- Function: `apply_flooring(image, flooring_type, flooring_data)`
  - Prompt enforces floor-only replacement with realism: correct perspective, lighting/shadows, clean edges, photorealism.
  - Uses `gemini-2.5-flash-image` and requests IMAGE-only output.
- Tests:
  - Single flooring type (e.g., dark walnut)
  - Multiple flooring types grid and side-by-side visualization
- Quality assessment:
  - Change region: bottom ~30% as floor
  - Preserve regions: ceiling/upper walls
  - Reuses SSIM/change/artifact metrics; aggregates with weights emphasizing preservation
- Outputs: images and per-run metadata JSONs in `output_images/flooring_tests`; CSV assessment and plots; comparison vs paint scenario.

## Notebook 5 — Cabinet/Furniture Replacement (`05_cabinet_furniture_replacement.ipynb`)

- Goals: replace kitchen cabinets and/or furniture while preserving everything else; maintain perspective/lighting; evaluate quality.
- Data:
  - `CABINET_STYLES` (white shaker, navy shaker, modern walnut, gray shaker, two-tone, glass-front)
  - `FURNITURE_STYLES` (styles for sofas/chairs, etc.)
- Function: `replace_cabinets(image, cabinet_key, cabinet_data)`
  - Prompt emphasizes cabinet-only replacement with detailed style/color/finish/hardware; preserve counters/appliances/walls/floor.
- Tests:
  - Single cabinet style
  - Multiple style grid visualization
- Quality assessment:
  - Approx cabinet change region; preserve floors/ceiling/counters
  - Weight preservation higher due to complexity
- Outputs: images/JSON in `output_images/furniture_tests` and CSV assessments.

## Notebook 6 — Lighting Scenarios (`06_lighting_scenarios.ipynb`)

- Goals: transform lighting only; compare natural vs artificial; warm vs cool; time-of-day progression; apply metrics focusing on structural preservation.
- Data: `LIGHTING_SCENARIOS` dict: bright daylight, soft morning, golden hour, overcast, warm evening, cool office, dramatic night, blue hour.
- Function: `apply_lighting(image, lighting_key, lighting_data)`
  - Prompt: change ONLY lighting with realistic physics (direction, temperature, falloff, reflections) while preserving all objects.
- Tests:
  - Single scenario (e.g., warm evening)
  - Time-of-day progression (morning → midday → golden hour → evening)
  - Temperature comparison (warm vs neutral vs cool)
- Metrics:
  - Structural preservation via grayscale SSIM over large regions
  - Global color/brightness shift via average RGB delta (warmth shift R−B; brightness)
  - Artifact detection reused
  - Overall score weighted heavily toward preservation
- Outputs: images and CSVs in `output_images/lighting_tests`.

## Notebook 7 — Color Scheme Testing (`07_color_scheme_testing.ipynb`)

- Goals: coordinated transformations (walls + floors), color palettes, complementary/analogous/monochromatic styles, client-ready comparisons.
- Data: `COLOR_SCHEMES` dict: modern gray & walnut, coastal white & light oak, warm traditional, dramatic navy & marble, Scandinavian white & gray LVP, earthy sage & terracotta.
- Function: `apply_color_scheme(image, scheme_key, scheme_data)`
  - Prompt applies walls and flooring changes together, preserves everything else, demands cohesion and realistic finish/lighting.
- Tests:
  - Single scheme application (before/after)
  - Multiple schemes grid with titles (style names)
- Metrics/assessment:
  - Change regions split into walls (upper) and floor (bottom)
  - Preserve ceiling/counters/appliances as applicable
  - Overall score balances preservation, change magnitude, and artifacts
- Outputs: images and CSVs in `output_images/color_scheme_tests`, plus markdown summaries with comparison tables.
- Wrap-up: “HomeVision Studio Complete” section summarizing all previous notebooks and next steps.

## Notebook 8 — Advanced Transformations (`08_advanced_transformations.ipynb`)

- Current state: empty placeholder (no cells yet). Intended future areas include backsplash/countertop materials, texture tests, batch processing, dashboards, etc.

## Prompt Party Nano Prototype (`prompt_party_nano_prototype.ipynb`)

- Purpose: analytics/iteration workflow inspired by PromptPartyNano; clones the reference repo, parses TypeScript configs, assembles prompt variants, stubs an LLM, scores variants, and writes artifacts.
- Steps:
  - Ensures local scientific stack; sets up `artifacts/` directory under repo root
  - Clones or fetches `https://github.com/NeoLudditeAI/PromptPartyNano.git` to `PromptPartyNano/`
  - Parses `types/index.ts` and `types/badges.ts` for `GAME_CONFIG` and `CAPABILITY_BADGES`
  - Assembles prompt variants across capability badges, tones, and detail levels
  - `LLMStub` emulates responses deterministically for offline experiments (no real API calls)
  - Annotates outcomes, computes accuracy/macro-F1 (rule-based), visualizes, and persists CSV/PNG artifacts in timestamped run folders

## How to run (quick reference)

1) Prepare environment and images
- Set env var: `GOOGLE_API_KEY` or `GEMINI_API_KEY` (don’t hardcode keys in notebooks or prompts)
- Place test images into `homevision_tests/input_images/`

2) Recommended order
- Notebook 1: setup, rules, sanity checks
- Notebook 2: paint (simplest and fastest iteration)
- Notebook 3: quality metrics + thresholds, visualize scoring
- Notebook 4: flooring replacement
- Notebook 5: cabinets/furniture replacement
- Notebook 6: lighting scenarios
- Notebook 7: coordinated color schemes
- Optional: Prompt Party Nano prototype for prompt analytics

3) Expected runtimes and gotchas
- Image edits require `gemini-2.5-flash-image`; `gemini-2.5-flash` returns text only
- Provide ≥1024×1024 images for better results
- Some metrics depend on approximate regions (percent boxes for walls/floors); adjust per photo composition
- Artifact detection thresholds (blur/edges) are heuristic and may need tuning by room type
- Rate limiting may apply; sleeps are used in loops to reduce API errors

## Core prompt contract (for reuse in other models)

When asking a model to edit images for interior transformations, enforce these rules:
- Photorealism only; no sketches or overlays
- Preserve camera perspective and spatial relationships
- Maintain lighting consistency and natural reflections/shadows
- Do not alter non-target areas; outside regions must remain pixel-identical
- Respect real-world materials and plausible construction details
- Return image-only output (no text or annotations in the image)

Common scenario intents with strict boundaries:
- Paint: “Change ALL walls to {brand} {color_name} ({color_code}), finish {finish}; preserve trim, floors, furniture, ceiling; photorealistic under {lighting_type} lighting.”
- Flooring: “Replace ONLY the floor with {material} — {description}, pattern {pattern}; enforce realistic perspective and clean edges; preserve walls/cabinets/furniture.”
- Cabinets: “Replace ALL kitchen cabinets with {style}/{color}/{finish}/{hardware}; preserve counters/appliances/walls/floor; ensure correct perspective and shadows.”
- Lighting: “Change ONLY lighting to {scenario_name}; keep all physical elements identical; ensure plausible direction, color temperature, falloff, and window luminance.”
- Color schemes: “Apply walls ({paint}) and floor ({flooring}) together; preserve everything else; ensure cohesive style {style} and mood {mood}.”

## Region definitions (percent-based boxes)

- Walls (paint): typically `{'x':10,'y':10,'width':80,'height':60}` (tune per photo)
- Floor (flooring): typically bottom 30% `{'x':0,'y':70,'width':100,'height':30}`
- Preserve regions: ceiling/upper wall strips, floors/counters depending on scenario

## Quality metrics (portable)

- Preservation (unchanged areas): SSIM in [0,100]
- Change magnitude (target area): mean absolute pixel diff in [0,100]
- Artifacts: Laplacian variance (sharpness), edge density, boolean flags → artifact score in [0,100]
- Color accuracy (paint-specific): Euclidean RGB distance inverted to 0–100
- Overall score: weighted by scenario; example weights:
  - Paint (with color): 35% preservation, 15% change, 25% artifacts, 25% color accuracy
  - Flooring: 45% preservation, 20% change, 35% artifacts
  - Cabinets: 50% preservation, 15% change, 35% artifacts
  - Lighting: 70% preservation, 30% artifacts (plus separate color/brightness shift diagnostics)
  - Color schemes: 40% preservation, 25% average change (walls+floor), 35% artifacts

Thresholds (current defaults; adjust per use-case):
- Production ready: Overall ≥85; preservation ≥90; artifacts ≥85
- Acceptable: Overall ≥75; preservation ≥80; artifacts ≥75

## Files and artifacts generated

- Edited images: `homevision_tests/output_images/<scenario>/*.png`
- Per-run metadata (some notebooks): JSON alongside images
- CSV metrics: in `homevision_tests/metrics/` or scenario folders with timestamps
- Visualizations: plotted inline; some notebooks write PNGs (e.g., Prompt Party Nano prototype saves plots under `artifacts/run_*/`)

## Safety and secrets

- Never include raw API keys in prompts or checked-in files.
- Use `GOOGLE_API_KEY` or `GEMINI_API_KEY` via environment or `.env` loaded by `python-dotenv`.
- When sharing this document externally, confirm it contains no secrets or private file paths beyond generic structure.

## Minimal prompt bundle (copy-ready)

Context summary:
- Images live under `homevision_tests/input_images/`; outputs saved under `homevision_tests/output_images/<scenario>`
- Use `gemini-2.5-flash-image` for edits; return image-only outputs
- Enforce strict photorealism, perspective, lighting consistency; preserve non-target areas pixel-perfect

Scenario prompts:
- Paint walls: Change ALL walls to {brand} {color_name} ({color_code}), finish {finish}. Preserve trim, floor, ceiling, furniture. Photorealistic under {lighting_type}. Output: edited image only.
- Flooring: Replace ONLY the floor with {material}: {description}; pattern {pattern}. Preserve walls, cabinets, furniture. Maintain perspective, realistic shadows/reflections. Output: edited image only.
- Cabinets: Replace ALL cabinets with {style}, color {color}, finish {finish}, hardware {hardware}. Preserve counters, appliances, walls, floor. Maintain perspective and realism. Output: edited image only.
- Lighting: Change ONLY lighting to {name}: {description}, time {time}, temperature {temperature}, intensity {intensity}, shadows {shadows}. Preserve all physical elements. Output: edited image only.
- Color scheme: Apply walls ({walls.color}, {walls.finish}) AND flooring ({flooring.material}: {flooring.description}, pattern {flooring.pattern}) in style {style}, mood {mood}. Preserve everything else. Output: edited image only.

Quality checks to apply after generation:
- Preservation: unchanged regions meet SSIM ≥90
- Artifacts: sharpness acceptable; edge density reasonable; no overlays/text
- Scenario-specific: walls/floor changed correctly; clean edges; realistic lighting and materials

---

If you need structured JSON instead of prose for downstream agents, I can export a machine-readable notebook inventory with key functions, prompts, and IO paths on request.