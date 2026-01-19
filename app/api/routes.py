from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.schemas import EvaluationRequest, EvaluationResponse
from app.services.evaluator import evaluate

router = APIRouter()
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/api/v1/evaluate", response_model=EvaluationResponse)
def evaluate_policy(payload: EvaluationRequest) -> EvaluationResponse:
    return evaluate(payload)
