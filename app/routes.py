"""Public HTML routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.config import GA_MEASUREMENT_ID
from app.content import load_public_content


templates = Jinja2Templates(directory="templates")
# Empty string means analytics is off. Templates only show the consent banner
# and the "Privacy choices" control when this is set.
templates.env.globals["ga_measurement_id"] = GA_MEASUREMENT_ID
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
        # Failed database: profile stays visible, but say so honestly with 503.
        status_code=503 if content.degraded else 200,
    )


@router.get("/privacy")
def privacy_page(request: Request):
    return templates.TemplateResponse(request=request, name="privacy.html")
