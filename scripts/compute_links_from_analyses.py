"""
Compute image-to-room links from a floor plan JSON and DB-aligned image analyses JSON.

This script replicates the improved feature-aware matching (no filename heuristics) used in the notebook.
It outputs links with per-candidate score breakdowns suitable for ingestion.

Usage (PowerShell):

  python -m scripts.compute_links_from_analyses `
    --floorplan-json "uploads/floor_plans/analysis/genMid.R2929648_1_4_analysis_gemini-2-5-flash_20251102_111958.json" `
    --analyses-json "uploads/analysis/image_analyses_db_aligned.json" `
    --output-links "uploads/analysis/image_room_links_v2.json"
"""

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from rapidfuzz import fuzz
except Exception:
    # Fallback simple ratio if rapidfuzz not available
    class _Fuzz:
        @staticmethod
        def partial_ratio(a: str, b: str) -> float:
            a = a.lower(); b = b.lower()
            if not a or not b:
                return 0.0
            if a in b or b in a:
                return 100.0
            return 0.0
    fuzz = _Fuzz()


def _tokens(s: str) -> Set[str]:
    return set(t for t in re.split(r"[^a-z0-9]+", (s or '').lower()) if t)

FEATURE_SYNONYMS = {
    'island': {'kitchen island', 'island'},
    'fireplace': {'fireplace', 'hearth'},
    'double vanity': {'double vanity', 'dual vanity'},
    'pantry': {'pantry'},
    'closet': {'closet', 'walk-in closet', 'walk in closet'},
    'shower': {'shower'},
    'tub': {'tub', 'bathtub', 'bath tub'},
    'stairs': {'stairs', 'staircase'},
    'sink': {'sink'},
    'range': {'range', 'stove', 'cooktop', 'oven'},
    'dishwasher': {'dishwasher'},
    'fridge': {'fridge', 'refrigerator'},
    'dryer': {'dryer'},
    'washer': {'washer', 'washing machine'},
}

FLOOR_TYPE_EQUIV = {
    'basement': {'basement', 'lower'},
    'ground': {'main', 'ground', 'first'},
    'upper': {'upper', 'second', 'third'},
}


def derive_feature_tags_from_db_aligned(analysis: Dict[str, Any]) -> Set[str]:
    tags: Set[str] = set(_tokens(' '.join(analysis.get('tags') or [])))
    # Include keywords
    tags |= _tokens(' '.join(analysis.get('keywords') or []))
    # From appliances/products
    for ap in analysis.get('appliances') or []:
        tags |= _tokens(' '.join([ap.get('type') or '', ap.get('brand') or '']))
    # From fixtures
    for fx in analysis.get('fixtures_visible') or []:
        tags |= _tokens(' '.join([fx.get('fixture_type') or '', fx.get('style') or '']))
    # From objects
    for obj in analysis.get('objects_detected') or []:
        tags |= _tokens(obj.get('label') or '')
        tags |= _tokens(obj.get('category') or '')
    # From description/name_hint
    tags |= _tokens(analysis.get('description') or '')
    tags |= _tokens(analysis.get('name_hint') or '')
    # Normalize via synonyms
    for feat, syns in FEATURE_SYNONYMS.items():
        if any(s in tags for s in syns):
            tags.add(feat)
    return tags


def size_similarity(analysis_dims: Dict[str, Any], room_dims: Dict[str, Any]) -> float:
    try:
        al = (analysis_dims or {}).get('length')
        aw = (analysis_dims or {}).get('width')
        rl = (room_dims or {}).get('length') or (room_dims or {}).get('length_ft')
        rw = (room_dims or {}).get('width') or (room_dims or {}).get('width_ft')
        if not all([al, aw, rl, rw]):
            return 0.0
        aa = float(al) * float(aw)
        ra = float(rl) * float(rw)
        if ra <= 0:
            return 0.0
        ratio = aa / ra
        return max(0.0, 1.0 - abs(math.log(max(ratio, 1e-6))))
    except Exception:
        return 0.0


def rank_candidates(analysis: Dict[str, Any], rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rtype = (analysis.get('room_type') or 'other').lower()
    fh = (analysis.get('floor_hint') or {})
    floor_type_hint = (fh.get('type') or '').lower()
    floor_number_hint = fh.get('number')
    name_hint = (analysis.get('name_hint') or '')

    itags = derive_feature_tags_from_db_aligned(analysis)
    ranked: List[Dict[str, Any]] = []

    for r in rooms:
        score = 0.0
        breakdown: Dict[str, float] = {}

        # Type matching
        rt = (r.get('room_type') or '').lower()
        if rtype and rt:
            if rtype == rt:
                breakdown['type_exact'] = 4.0; score += 4.0
            elif rtype in rt:
                breakdown['type_partial'] = 2.0; score += 2.0

        # Floor number
        if floor_number_hint is not None and r.get('floor_number') is not None:
            if int(floor_number_hint) == int(r['floor_number']):
                breakdown['floor_number'] = 2.0; score += 2.0

        # Floor type group
        if floor_type_hint and r.get('floor_type'):
            for group, equiv in FLOOR_TYPE_EQUIV.items():
                if floor_type_hint in equiv and (r['floor_type'] or '').lower() in equiv:
                    breakdown['floor_type'] = breakdown.get('floor_type', 0.0) + 1.0; score += 1.0
                    break

        # Features overlap
        rfeats = set(_tokens(' '.join(r.get('features') or [])))
        overlap = len(itags & rfeats)
        if overlap:
            pts = min(3.0, overlap * 1.0)
            breakdown['features_overlap'] = pts; score += pts

        # Name/label fuzzy
        label = (r.get('label_ocr') or r.get('name') or '').lower()
        if label and (name_hint or itags):
            needle = ' '.join([name_hint] + list(itags))
            fr = (fuzz.partial_ratio(needle, label) / 100.0) * 2.0
            if fr > 0:
                breakdown['name_fuzzy'] = round(fr, 3); score += fr

        # Primary hint
        if any(x in itags or x in _tokens(name_hint) for x in {'primary','master'}):
            nm = (r.get('name') or '').lower()
            if 'primary' in nm or 'master' in nm:
                breakdown['primary_name'] = 1.5; score += 1.5

        # Size similarity (if approx dims provided in analysis.spatial_cues and room has measured)
        sim = size_similarity((analysis.get('spatial_cues') or {}).get('approx_dimensions_ft') or {}, r.get('measured_dimensions') or {})
        if sim > 0:
            add = round(2.0 * sim, 3)
            breakdown['size_similarity'] = add; score += add

        if score > 0:
            ranked.append({
                'room_id': r['id'],
                'room_name': r.get('name') or '',
                'room_type': r.get('room_type') or '',
                'floor_number': r.get('floor_number'),
                'floor_type': r.get('floor_type') or '',
                'score': round(score, 3),
                'breakdown': breakdown,
            })

    ranked.sort(key=lambda x: x['score'], reverse=True)
    return ranked


def build_room_index_from_floorplan(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    rooms: List[Dict[str, Any]] = []
    for fl in doc.get('floors', []) or []:
        meta = {
            'floor_number': fl.get('floor_number'),
            'floor_type': fl.get('floor_type'),
            'floor_name': fl.get('floor_name'),
        }
        for r in fl.get('rooms', []) or []:
            entry = {
                'id': r.get('id'),
                'name': r.get('name'),
                'label_ocr': r.get('label_ocr'),
                'room_type': (r.get('room_type') or '').lower(),
                'floor_number': meta['floor_number'],
                'floor_type': meta['floor_type'],
                'floor_name': meta['floor_name'],
                'features': r.get('features') or [],
                'measured_dimensions': r.get('measured_dimensions') or {},
            }
            rooms.append(entry)
    return rooms


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--floorplan-json', type=str, required=True)
    parser.add_argument('--analyses-json', type=str, required=True)
    parser.add_argument('--output-links', type=str, required=True)
    args = parser.parse_args()

    floorplan_path = Path(args.floorplan_json)
    analyses_path = Path(args.analyses_json)
    out_path = Path(args.output_links)

    if not floorplan_path.exists():
        raise SystemExit(f"Floorplan JSON not found: {floorplan_path}")
    if not analyses_path.exists():
        raise SystemExit(f"Analyses JSON not found: {analyses_path}")

    with open(floorplan_path, 'r', encoding='utf-8') as f:
        floorplan = json.load(f)
    with open(analyses_path, 'r', encoding='utf-8') as f:
        analyses = json.load(f)

    room_index = build_room_index_from_floorplan(floorplan)

    links: List[Dict[str, Any]] = []
    for rec in analyses:
        # Normalize expected analysis view
        a = {
            'room_type': ((rec.get('room_analysis') or {}).get('room_type_detected') or 'other'),
            'floor_hint': (rec.get('extras') or {}).get('floor_hint') or {},
            'name_hint': (rec.get('extras') or {}).get('name_hint') or '',
            'tags': (rec.get('image_analysis') or {}).get('keywords') or [],
            'style': (rec.get('room_analysis') or {}).get('style'),
            'description': (rec.get('image_analysis') or {}).get('description'),
            'color_palette': (rec.get('room_analysis') or {}).get('color_palette') or {},
            'dominant_colors': (rec.get('image_analysis') or {}).get('dominant_colors') or [],
            'materials_visible': (rec.get('image_analysis') or {}).get('materials_visible') or [],
            'fixtures_visible': (rec.get('image_analysis') or {}).get('fixtures_visible') or [],
            'appliances': (rec.get('room_analysis') or {}).get('products_detected') or [],
            'objects_detected': (rec.get('image_analysis') or {}).get('objects_detected') or [],
            'spatial_cues': (rec.get('extras') or {}).get('spatial_cues') or {},
            'view_angle': (rec.get('image_analysis') or {}).get('view_angle'),
            'estimated_coverage': (rec.get('image_analysis') or {}).get('estimated_coverage'),
            'lighting_quality': (rec.get('image_analysis') or {}).get('lighting_quality'),
            'image_quality_score': (rec.get('image_analysis') or {}).get('image_quality_score'),
            'clarity': (rec.get('image_analysis') or {}).get('clarity'),
            'confidence': (rec.get('image_analysis') or {}).get('confidence_score') or 0.0,
        }
        ranked = rank_candidates(a, room_index)
        links.append({
            'image': rec.get('image'),
            'filename': rec.get('filename'),
            'analysis': a,
            'candidates': ranked[:3],
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(links, f, indent=2)

    print(f"Saved {len(links)} links to {out_path}")


if __name__ == '__main__':
    main()
