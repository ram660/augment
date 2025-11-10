"""
Documents API endpoints for uploading and parsing documents with MarkItDown.

Endpoints (all require auth):
- POST /api/v1/documents/parse
- POST /api/v1/documents/contractor-quote/parse
- POST /api/v1/documents/datasheet/parse
- POST /api/v1/documents/inspection/parse

Files are saved under uploads/documents/<uuid>.<ext> temporarily for parsing.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.api.auth import get_current_user
from backend.models.user import User
from backend.services.document_parser_service import (
    DocumentParserService,
    DocumentParseError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


async def _save_upload_file(upload_file: UploadFile, destination: Path) -> str:
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = await upload_file.read()
        with open(destination, "wb") as f:
            f.write(content)
        return str(destination)
    except Exception as e:  # pragma: no cover
        logger.error("Error saving uploaded file: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")


def _dest_path(filename: str | None) -> Path:
    ext = ".bin"
    if filename and "." in filename:
        ext = "." + filename.split(".")[-1]
    return Path("uploads/documents") / f"{uuid4()}{ext}"


@router.post("/parse")
async def parse_document(file: UploadFile = File(...), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    dest = _dest_path(file.filename)
    saved = await _save_upload_file(file, dest)
    try:
        svc = DocumentParserService()
        parsed = await svc.parse(saved)
        return {"status": "ok", "parsed": parsed, "path": saved}
    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # pragma: no cover
        logger.error("Parse failed: %s", e)
        raise HTTPException(status_code=500, detail="Document parse failed")


@router.post("/contractor-quote/parse")
async def parse_contractor_quote(file: UploadFile = File(...), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    dest = _dest_path(file.filename)
    saved = await _save_upload_file(file, dest)
    try:
        svc = DocumentParserService()
        parsed = await svc.parse_contractor_quote(saved)
        return {"status": "ok", "parsed": parsed, "path": saved}
    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # pragma: no cover
        logger.error("Contractor quote parse failed: %s", e)
        raise HTTPException(status_code=500, detail="Contractor quote parse failed")


@router.post("/datasheet/parse")
async def parse_datasheet(file: UploadFile = File(...), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    dest = _dest_path(file.filename)
    saved = await _save_upload_file(file, dest)
    try:
        svc = DocumentParserService()
        parsed = await svc.parse_product_datasheet(saved)
        return {"status": "ok", "parsed": parsed, "path": saved}
    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # pragma: no cover
        logger.error("Datasheet parse failed: %s", e)
        raise HTTPException(status_code=500, detail="Datasheet parse failed")


@router.post("/inspection/parse")
async def parse_inspection(file: UploadFile = File(...), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    dest = _dest_path(file.filename)
    saved = await _save_upload_file(file, dest)
    try:
        svc = DocumentParserService()
        parsed = await svc.parse_inspection_report(saved)
        return {"status": "ok", "parsed": parsed, "path": saved}
    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # pragma: no cover
        logger.error("Inspection parse failed: %s", e)
        raise HTTPException(status_code=500, detail="Inspection parse failed")




@router.post("/quotes/compare")
async def compare_quotes(files: List[UploadFile] = File(...), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    if not files or len(files) < 2:
        raise HTTPException(status_code=400, detail="Upload at least two quote files to compare")
    svc = DocumentParserService()
    saved_paths: List[str] = []
    try:
        for f in files:
            dest = _dest_path(f.filename)
            saved = await _save_upload_file(f, dest)
            saved_paths.append(saved)
        result = await svc.compare_quotes(saved_paths)
        return {"status": "ok", "result": result, "paths": saved_paths}
    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # pragma: no cover
        logger.error("Quotes comparison failed: %s", e)
        raise HTTPException(status_code=500, detail="Quotes comparison failed")


@router.post("/chat")
async def chat_with_document(
    file: UploadFile = File(...),
    question: str = Form(...),
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    dest = _dest_path(file.filename)
    saved = await _save_upload_file(file, dest)
    try:
        svc = DocumentParserService()
        answer = await svc.chat_with_document(saved, question)
        return {"status": "ok", "answer": answer, "path": saved}
    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # pragma: no cover
        logger.error("Chat with document failed: %s", e)
        raise HTTPException(status_code=500, detail="Chat with document failed")


@router.post("/manual/parse")
async def parse_manual(file: UploadFile = File(...), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    dest = _dest_path(file.filename)
    saved = await _save_upload_file(file, dest)
    try:
        svc = DocumentParserService()
        parsed = await svc.parse_manual(saved)
        return {"status": "ok", "parsed": parsed, "path": saved}
    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # pragma: no cover
        logger.error("Manual parse failed: %s", e)
        raise HTTPException(status_code=500, detail="Manual parse failed")
