"""
Utilities for linking room images to rooms using feature-aware matching.

Extracted from the compute_links script for reuse in API/services.
"""
from typing import Any, Dict, List, Set
import math
import re

try:
    from rapidfuzz import fuzz as _fuzz
    def _fuzzy(a: str, b: str) -> float:
        return (_fuzz.partial_ratio(a, b) or 0.0) / 100.0
except Exception:
    def _fuzzy(a: str, b: str) -> float:
        a = a.lower(); b = b.lower()
        if not a or not b:
            return 0.0
        return 1.0 if (a in b or b in a) else 0.0


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


def derive_feature_tags_from_db_aligned(analysis: Dict[str, Any]) -> Set[str]:
    tags: Set[str] = set(_tokens(' '.join(analysis.get('tags') or [])))
    tags |= _tokens(' '.join(analysis.get('keywords') or []))
    for ap in analysis.get('appliances') or []:
        tags |= _tokens(' '.join([ap.get('type') or '', ap.get('brand') or '']))
    for fx in analysis.get('fixtures_visible') or []:
        tags |= _tokens(' '.join([fx.get('fixture_type') or '', fx.get('style') or '']))
    for obj in analysis.get('objects_detected') or []:
        tags |= _tokens(obj.get('label') or '')
        tags |= _tokens(obj.get('category') or '')
    tags |= _tokens(analysis.get('description') or '')
    tags |= _tokens(analysis.get('name_hint') or '')
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
            fr = _fuzzy(needle, label) * 2.0
            if fr > 0:
                breakdown['name_fuzzy'] = round(fr, 3); score += fr

        # Primary hint
        if any(x in itags or x in _tokens(name_hint) for x in {'primary','master'}):
            nm = (r.get('name') or '').lower()
            if 'primary' in nm or 'master' in nm:
                breakdown['primary_name'] = 1.5; score += 1.5

        # Size similarity
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
