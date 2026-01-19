# Stakeholder Impact Dashboard (Sprint 0)

Sprint 0 delivers a minimal FastAPI app with a single-page UI and a stubbed
evaluation API. The responses are deterministic placeholders to support early
workflow validation.

## Setup

```bash
python -m venv .venv
```

```bash
.\.venv\Scripts\Activate.ps1
```

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/`.

## Endpoints

- `GET /health` -> `{ "status": "ok" }`
- `GET /` -> HTML UI
- `POST /api/v1/evaluate` -> stubbed evaluation response

## Notes

Sprint 0 uses placeholder metrics and narratives. Sprint 1 will introduce real
stakeholder impact calculations.
