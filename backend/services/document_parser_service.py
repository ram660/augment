"""
Document Parser Service using Microsoft MarkItDown (optional dependency).

Phase 1 foundation for parsing uploaded documents (PDF/Word/Images) into
Markdown and extracting structured fields for common HomeView AI use cases:
- Contractor quotes (line items, totals)
- Product datasheets (model/specs/dimensions)
- Inspection reports (issues/recommendations)

If markitdown is not installed, methods raise a clear error instructing how to
install it. We intentionally keep extraction heuristics lightweight and
fail-safe. Callers should wrap in try/except and degrade gracefully.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
from backend.integrations.gemini import GeminiClient


try:  # Optional dependency
    from markitdown import MarkItDown  # type: ignore
except Exception:  # pragma: no cover - handled at runtime if MarkItDown missing
    MarkItDown = None  # type: ignore


class DocumentParseError(RuntimeError):
    pass


@dataclass
class ParsedDocument:
    markdown: str
    meta: Dict[str, Any]


class DocumentParserService:
    """Thin wrapper around MarkItDown with simple extractors for common docs."""

    def __init__(self) -> None:
        if MarkItDown is None:
            raise DocumentParseError(
                "MarkItDown is required for document parsing. Install with: pip install markitdown"
            )
        self._md = MarkItDown()

    async def parse(self, file_path: str | Path) -> Dict[str, Any]:
        """Convert a file to Markdown and return basic payload."""
        p = str(file_path)
        try:
            res = self._md.convert(p)
            markdown = getattr(res, "text_content", None)
            if markdown is None:
                markdown = str(res) if res is not None else ""
            return {"markdown": markdown, "meta": {"source_path": p}}
        except Exception as e:  # pragma: no cover
            logger.error("MarkItDown conversion failed: %s", e)
            raise DocumentParseError(str(e))

    async def parse_contractor_quote(self, file_path: str | Path) -> Dict[str, Any]:
        """Parse a contractor quote into items and totals (best-effort heuristics)."""
        base = await self.parse(file_path)
        md = base.get("markdown") or ""
        items = self._extract_table_items(md)
        totals = self._extract_totals(md)
        summary = self._quote_summary(items, totals)
        return {"markdown": md, "items": items, "totals": totals, "summary": summary}

    async def parse_product_datasheet(self, file_path: str | Path) -> Dict[str, Any]:
        """Parse a product datasheet for specs and dimensions (best-effort)."""
        base = await self.parse(file_path)
        md = base.get("markdown") or ""
        specs = self._extract_kv_specs(md)
        dims = self._extract_dimensions(md)
        summary = self._datasheet_summary(specs, dims)
        return {"markdown": md, "specs": specs, "dimensions": dims, "summary": summary}

    async def parse_inspection_report(self, file_path: str | Path) -> Dict[str, Any]:
        """Parse an inspection report for issues and recommendations (best-effort)."""
        base = await self.parse(file_path)
        md = base.get("markdown") or ""
        issues = self._extract_bullets(md, headings=("defects", "issues", "concerns"))
        recs = self._extract_bullets(md, headings=("recommendations", "suggestions", "actions"))
        summary = self._inspection_summary(issues, recs)
        return {"markdown": md, "issues": issues, "recommendations": recs, "summary": summary}

    # ----------------------- Heuristics ----------------------- #

    def _extract_table_items(self, md: str) -> List[Dict[str, Any]]:
        """Parse GitHub-style tables into items with qty/price/total if present."""
        items: List[Dict[str, Any]] = []
        lines = md.splitlines()
        for i in range(len(lines) - 2):
            header = lines[i].strip().lower()
            sep = lines[i + 1].strip()
            row = lines[i + 2].strip()
            if header.startswith("|") and sep.startswith("|") and row.startswith("|") and set(sep.replace("|", "").strip()) <= {"-", ":"}:
                cols = [c.strip().lower() for c in header.strip("|").split("|")]
                for j in range(i + 2, len(lines)):
                    r = lines[j].strip()
                    if not r.startswith("|"):
                        break
                    vals = [v.strip() for v in r.strip("|").split("|")]
                    obj: Dict[str, Any] = {}
                    for k, col in enumerate(cols):
                        if k < len(vals):
                            obj[col] = vals[k]
                    if obj:
                        # Normalize qty/price/total if present
                        if "qty" in obj:
                            obj["qty"] = self._to_number(obj["qty"]) or obj["qty"]
                        for price_key in ("price", "unit price", "unit_price", "cost"):
                            if price_key in obj:
                                obj[price_key] = self._money_to_float(obj[price_key]) or obj[price_key]
                        if "total" in obj:
                            obj["total"] = self._money_to_float(obj["total"]) or obj["total"]
                        items.append(obj)
        # Fallback: bullet list with price
        if not items:
            for line in lines:
                m = re.search(r"\$\s*([0-9][0-9,]*(?:\.[0-9]{2})?)", line)
                if m:
                    items.append({"description": line.strip(), "total": float(m.group(1).replace(",", ""))})
        return items

    def _extract_totals(self, md: str) -> Dict[str, Optional[float]]:
        totals: Dict[str, Optional[float]] = {"subtotal": None, "tax": None, "total": None}
        text = md.lower()
        def find_amount(patterns: List[str]) -> Optional[float]:
            for p in patterns:
                m = re.search(p, text, flags=re.IGNORECASE)
                if m:
                    val = m.group(1) or m.group(2)
                    try:
                        return float(val.replace(",", ""))
                    except Exception:
                        continue
            return None
        totals["subtotal"] = find_amount([r"subtotal[^\d$]*\$?\s*([0-9][\d,]*(?:\.[0-9]{2})?)", r"sub-total[^\d$]*\$?\s*([0-9][\d,]*(?:\.[0-9]{2})?)"])
        totals["tax"] = find_amount([r"tax[^\d$]*\$?\s*([0-9][\d,]*(?:\.[0-9]{2})?)"])
        totals["total"] = find_amount([r"grand\s*total[^\d$]*\$?\s*([0-9][\d,]*(?:\.[0-9]{2})?)", r"[^a-z]total[^\d$]*\$?\s*([0-9][\d,]*(?:\.[0-9]{2})?)"])
        return totals

    def _extract_kv_specs(self, md: str) -> Dict[str, str]:
        specs: Dict[str, str] = {}
        for line in md.splitlines():
            m = re.match(r"\s*([A-Za-z][A-Za-z0-9 _\-/]+)\s*[:|]\s*(.+)$", line)
            if m:
                key = m.group(1).strip().lower().replace(" ", "_")
                val = m.group(2).strip()
                if len(key) <= 48 and len(val) <= 200:
                    specs[key] = val
        return specs

    def _extract_dimensions(self, md: str) -> Dict[str, Optional[float]]:
        dims: Dict[str, Optional[float]] = {"width_in": None, "height_in": None, "depth_in": None}
        # Look for patterns like 30 in, 30", 30-inch; units in inches or mm
        mm_to_in = 0.0393701
        for line in md.splitlines():
            for label in ("width", "height", "depth"):
                m_in = re.search(rf"{label}[^\d]*([0-9]+(?:\.[0-9]+)?)\s*(in|\")", line, flags=re.IGNORECASE)
                m_mm = re.search(rf"{label}[^\d]*([0-9]+(?:\.[0-9]+)?)\s*mm", line, flags=re.IGNORECASE)
                if m_in:
                    dims[f"{label}_in"] = float(m_in.group(1))
                elif m_mm:
                    dims[f"{label}_in"] = round(float(m_mm.group(1)) * mm_to_in, 2)
        return dims

    def _extract_bullets(self, md: str, headings: tuple[str, ...]) -> List[str]:
        found: List[str] = []
        active = False
        for line in md.splitlines():
            if any(h in line.strip().lower() for h in headings):
                active = True
                continue
            if active:
                if line.strip().startswith(("- ", "* ")):
                    found.append(line.strip()[2:].strip())
                elif line.strip() == "":
                    active = False
        # Fallback: collect bullets from the whole doc if no section found
        if not found:
            for line in md.splitlines():
                if line.strip().startswith(("- ", "* ")):
                    found.append(line.strip()[2:].strip())
        return found[:20]

    # ----------------------- Summaries ----------------------- #

    def _quote_summary(self, items: List[Dict[str, Any]], totals: Dict[str, Optional[float]]) -> str:
        parts: List[str] = []
        if items:
            parts.append(f"{len(items)} items")
        if totals.get("subtotal"):
            parts.append(f"subtotal ${totals['subtotal']:.2f}")
        if totals.get("tax"):
            parts.append(f"tax ${totals['tax']:.2f}")
        if totals.get("total"):
            parts.append(f"total ${totals['total']:.2f}")
        return ", ".join(parts)

    def _datasheet_summary(self, specs: Dict[str, str], dims: Dict[str, Optional[float]]) -> str:
        parts: List[str] = []
        for key in ("model", "brand", "material", "finish"):
            if specs.get(key):
                parts.append(f"{key}: {specs[key]}")
        if any(dims.values()):
            w = dims.get("width_in")
            h = dims.get("height_in")
            d = dims.get("depth_in")
            sized = " x ".join(str(x) for x in [w, h, d] if x)
            if sized:
                parts.append(f"dimensions: {sized} in")
        return ", ".join(parts)

    def _inspection_summary(self, issues: List[str], recs: List[str]) -> str:
        p: List[str] = []
        if issues:
            p.append(f"issues: {len(issues)}")
        if recs:
            p.append(f"recommendations: {len(recs)}")
        return ", ".join(p)

    # ----------------------- Utilities ----------------------- #

    def _to_number(self, s: str) -> Optional[float]:
        try:
            return float(str(s).replace(",", "").strip())
        except Exception:
            return None

    def _money_to_float(self, s: str) -> Optional[float]:
        m = re.search(r"([0-9][0-9,]*(?:\.[0-9]{2})?)", str(s))
        if not m:
            return None
        try:
            return float(m.group(1).replace(",", ""))
        except Exception:
            return None



    # ----------------------- Enhancements ----------------------- #

    async def compare_quotes(self, file_paths: List[str | Path]) -> Dict[str, Any]:
        """Compare multiple contractor quotes and summarize differences.
        Returns per-quote parsed data plus a simple best-by-total indicator.
        """
        parsed: List[Dict[str, Any]] = []
        for p in file_paths:
            try:
                res = await self.parse_contractor_quote(p)
            except Exception as e:
                res = {"markdown": "", "items": [], "totals": {}, "summary": "", "error": str(e)}
            res["source_path"] = str(p)
            t = res.get("totals") or {}
            total = None
            if isinstance(t, dict):
                total = t.get("total") or t.get("subtotal")
            res["computed_total"] = total
            parsed.append(res)

        totals = [q.get("computed_total") for q in parsed if q.get("computed_total") is not None]
        best_index = None
        if totals:
            min_val = min(totals)
            for i, q in enumerate(parsed):
                if q.get("computed_total") == min_val:
                    best_index = i
                    break

        # Build a lightweight item catalog across quotes
        item_catalog: Dict[str, Dict[str, Any]] = {}
        for q in parsed:
            for it in q.get("items") or []:
                desc = str(it.get("description") or it.get("item") or "").strip().lower()
                if not desc:
                    continue
                entry = item_catalog.setdefault(desc, {"count": 0, "examples": []})
                entry["count"] += 1
                if "total" in it and len(entry["examples"]) < 3:
                    entry["examples"].append(it["total"])

        return {"quotes": parsed, "best_index": best_index, "item_catalog": item_catalog}

    async def parse_manual(self, file_path: str | Path) -> Dict[str, Any]:
        """Parse a DIY manual for tools, materials, and step-by-step instructions."""
        base = await self.parse(file_path)
        md = base.get("markdown") or ""
        tools = self._section_list(md, ("tools", "what you need", "you will need"))
        materials = self._section_list(md, ("materials", "supplies"))
        steps = self._numbered_steps(md)
        return {"markdown": md, "tools": tools, "materials": materials, "steps": steps}

    def _section_list(self, md: str, headings: tuple[str, ...]) -> List[str]:
        items: List[str] = []
        active = False
        for line in md.splitlines():
            if any(h in line.strip().lower() for h in headings):
                active = True
                continue
            if active:
                if line.strip().startswith(("- ", "* ")):
                    items.append(line.strip()[2:].strip())
                elif re.match(r"\d+[\.)]\s", line.strip()):
                    break
                elif line.strip() == "" and items:
                    break
        return items[:50]

    def _numbered_steps(self, md: str) -> List[str]:
        steps: List[str] = []
        for line in md.splitlines():
            m = re.match(r"\s*(\d+)[\.)]\s+(.*)", line)
            if m:
                steps.append(m.group(2).strip())
        if not steps:
            steps = self._extract_bullets(md, headings=("steps", "procedure", "instructions"))
        return steps[:100]

    async def chat_with_document(self, file_path: str | Path, question: str) -> Dict[str, Any]:
        """Answer a question grounded strictly in the provided document content using Gemini.
        Follows official Gemini text generation usage.
        """
        base = await self.parse(file_path)
        md = base.get("markdown") or ""

        system_instruction = (
            "You are a helpful assistant for HomeView AI. Answer the user's question "
            "using ONLY the provided document content. If the answer is not present, "
            "say 'Not found in document.' Be concise and include short quotes when helpful."
        )
        # Keep prompt within safe length; truncate if necessary
        doc_excerpt = md[:15000]
        prompt = f"Document (markdown):\n{doc_excerpt}\n\nQuestion: {question}\nAnswer:"

        gemini = GeminiClient()
        answer = await gemini.generate_text(
            prompt=prompt,
            temperature=0.2,
            system_instruction=system_instruction,
        )
        return {"answer": answer}
