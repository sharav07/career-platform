"""Public HTML routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.content import load_public_content


templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/")
def resume_page(request: Request):
    content = load_public_content(
        request.app.state.database_path,
        request.app.state.seed_path,
    )
    return templates.TemplateResponse(
        request=request,
        name="resume.html",
        context={"content": content},
    )
