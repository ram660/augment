"""
Analyze room images with the RoomAnalysisAgent and emit DB-aligned JSON records (no DB writes).
Requires GOOGLE_API_KEY or GEMINI_API_KEY.

Usage (PowerShell):
  python -m scripts.analyze_images_to_db_aligned \
    --directory "uploads/room_images" \
    --output "uploads/analysis/image_analyses_db_aligned.json" \
    --limit 5
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List

# Ensure repo root is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
import sys
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.agents.digital_twin.room_analysis_agent import RoomAnalysisAgent


def _db_aligned_from_agent(image_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    vc = data.get("visual_characteristics", {}) or {}
    dims = data.get("dimensions", {}) or {}
    spatial = data.get("spatial_features", {}) or {}

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
                "counts": {
                    "windows": None,
                    "doors": None,
                },
                "adjacency_hints": [],
            },
            "name_hint": "",
        }
    }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=str, default='uploads/room_images')
    parser.add_argument('--output', type=str, default='uploads/analysis/image_analyses_db_aligned.json')
    parser.add_argument('--limit', type=int, default=5)
    args = parser.parse_args()

    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        raise SystemExit("Set GOOGLE_API_KEY or GEMINI_API_KEY before running.")

    agent = RoomAnalysisAgent()

    images_dir = Path(args.directory)
    if not images_dir.exists():
        raise SystemExit(f"Directory not found: {images_dir}")

    all_images = sorted([str(p) for p in images_dir.glob('**/*') if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}])
    sample = all_images[: args.limit]

    outputs: List[Dict[str, Any]] = []
    for img in sample:
        resp = await agent.execute({
            "image": img,
            "room_type": "unknown",
            "analysis_type": "comprehensive",
        })
        if not resp.success:
            print(f"Analysis failed for {Path(img).name}: {resp.error}")
            continue
        outputs.append(_db_aligned_from_agent(img, resp.data or {}))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(outputs, f, indent=2)

    print(f"Saved {len(outputs)} DB-aligned analyses to {out_path}")


if __name__ == '__main__':
    asyncio.run(main())
