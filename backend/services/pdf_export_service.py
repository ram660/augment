"""
PDF Export Service

Exports a structured DIY guide (dict) to a nicely formatted PDF with optional
images. Uses ReportLab if installed. If ReportLab is not installed, raises a
clear error instructing how to install it.

Official docs for Gemini are at https://ai.google.dev/gemini-api/docs; this
service does not call Gemini directly, but is used by chat flows that may use
Gemini for content generation.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, ListFlowable, ListItem
    from reportlab.lib.units import inch
    from reportlab.lib import colors
except Exception:  # pragma: no cover - handled at runtime if ReportLab is missing
    letter = None
    getSampleStyleSheet = None
    SimpleDocTemplate = None
    Paragraph = None
    Spacer = None
    RLImage = None
    ListFlowable = None
    ListItem = None
    inch = None
    colors = None


class PDFExportError(RuntimeError):
    pass


def export_guide_to_pdf(
    guide: Dict[str, Any],
    image_paths: Optional[List[str]] = None,
    output_dir: str = "uploads/pdfs",
) -> str:
    """
    Export a DIY guide dict to a PDF and return the portable file path (e.g., 'uploads/pdfs/xxx.pdf').

    Args:
        guide: DIY guide dict with keys: title, summary, materials, tools, steps, safety_tips, etc.
        image_paths: Optional list of local image file paths to include.
        output_dir: Directory (relative to repo root) to write PDFs into.

    Returns:
        Relative file path to the generated PDF (for serving via StaticFiles).
    """
    if SimpleDocTemplate is None:
        raise PDFExportError(
            "ReportLab is required for PDF export. Please install with: pip install reportlab"
        )

    # Ensure output directory exists
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Build a filename
    title = (guide.get("title") or "DIY_Guide").strip().replace(" ", "_")[:64]
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{title}_{ts}.pdf"
    pdf_path = output_dir_path / filename

    # Prepare document
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=48, rightMargin=48, topMargin=48, bottomMargin=48)
    styles = getSampleStyleSheet()
    story: List[Any] = []

    # Title
    story.append(Paragraph(guide.get("title") or "DIY Project Plan", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))

    # Summary
    summary = guide.get("summary") or ""
    if summary:
        story.append(Paragraph("Summary", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(summary, styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))

    # Meta details
    meta_lines = []
    if guide.get("room_type"):
        meta_lines.append(f"Room: {guide['room_type']}")
    if guide.get("skill_level"):
        meta_lines.append(f"Skill level: {guide['skill_level']}")
    if guide.get("estimated_time_hours"):
        meta_lines.append(f"Estimated time: {guide['estimated_time_hours']} hours")
    if guide.get("estimated_cost_range"):
        meta_lines.append(f"Estimated cost: {guide['estimated_cost_range']}")

    if meta_lines:
        story.append(Paragraph("Details", styles["Heading2"]))
        for line in meta_lines:
            story.append(Paragraph(line, styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))

    # Materials
    materials = guide.get("materials") or []
    if materials:
        story.append(Paragraph("Materials", styles["Heading2"]))
        mat_items = []
        for m in materials:
            name = m.get("name") or "Material"
            qty = m.get("quantity")
            notes = m.get("notes")
            text = name
            if qty:
                text += f" — {qty}"
            if notes:
                text += f" ({notes})"
            mat_items.append(ListItem(Paragraph(text, styles["BodyText"])) )
        story.append(ListFlowable(mat_items, bulletType='bullet'))
        story.append(Spacer(1, 0.2 * inch))

    # Tools
    tools = guide.get("tools") or []
    if tools:
        story.append(Paragraph("Tools", styles["Heading2"]))
        tool_items = []
        for t in tools:
            name = t.get("name") or "Tool"
            opt = t.get("optional")
            notes = t.get("notes")
            text = name
            if opt:
                text += " (optional)"
            if notes:
                text += f" — {notes}"
            tool_items.append(ListItem(Paragraph(text, styles["BodyText"])) )
        story.append(ListFlowable(tool_items, bulletType='bullet'))
        story.append(Spacer(1, 0.2 * inch))

    # Steps
    steps = guide.get("steps") or []
    if steps:
        story.append(Paragraph("Steps", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))
        for idx, step in enumerate(steps, start=1):
            title = step.get("title") or f"Step {idx}"
            instr = step.get("instructions") or ""
            dur = step.get("duration_estimate_minutes")
            story.append(Paragraph(f"{idx}. {title}", styles["Heading3"]))
            if dur:
                story.append(Paragraph(f"Estimated duration: {dur} minutes", styles["BodyText"]))
            story.append(Paragraph(instr, styles["BodyText"]))
            story.append(Spacer(1, 0.1 * inch))
        story.append(Spacer(1, 0.2 * inch))

    # Safety Tips
    safety = guide.get("safety_tips") or []
    if safety:
        story.append(Paragraph("Safety Tips", styles["Heading2"]))
        safe_items = [ListItem(Paragraph(t, styles["BodyText"])) for t in safety]
        story.append(ListFlowable(safe_items, bulletType='bullet'))
        story.append(Spacer(1, 0.2 * inch))

    # Images (if provided)
    if image_paths:
        story.append(Paragraph("Images", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))
        for p in image_paths:
            try:
                # Constrain width for the page
                story.append(RLImage(p, width=6.5 * inch, preserveAspectRatio=True, mask='auto'))
                story.append(Spacer(1, 0.2 * inch))
            except Exception as e:  # ignore bad images
                logger.warning("Skipping image in PDF (%s): %s", p, e)

    # Build PDF
    doc.build(story)

    # Return relative path usable by StaticFiles
    rel_path = str(pdf_path).replace("\\", "/")
    if not rel_path.startswith("uploads/"):
        # make it portable as StaticFiles likely serves /uploads
        rel_path = f"uploads/pdfs/{pdf_path.name}"

    logger.info("PDF generated at: %s", rel_path)
    return rel_path

