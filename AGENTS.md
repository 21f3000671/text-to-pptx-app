# Repository Guidelines

## Project Structure & Modules
- `app/main.py`: FastAPI entry; routes `/`, `/health`, `/generate`.
- `app/engine/`: LLM routing and PPTX builder (`outline.py`, `slide_builder.py`, `llm_router.py`).
- `templates/`: Jinja templates (UI at `index.html`).
- `static/`: Frontend assets (`app.js`, `styles.css`).
- `requirements.txt`, `Dockerfile`, `Procfile`, `LICENSE`, `README.md` at repo root.

## Build, Run, and Dev
- Create env and install deps:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Run locally:
  - `uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - Open `http://localhost:8000` (UI), or `curl localhost:8000/health`.
- Docker:
  - `docker build -t text-to-pptx .`
  - `docker run -p 8000:8000 text-to-pptx`
- Procfile-compatible platforms use `web: uvicorn app.main:app --port $PORT`.

## Coding Style & Naming
- Python 3.11; follow PEP 8 with 4-space indents and type hints where practical.
- Modules and files: `snake_case.py`; classes: `PascalCase`; functions/vars: `snake_case`.
- Templates and static files keep minimal dependencies; avoid heavy front-end frameworks.
- Optional tools (not enforced): format with `black`, lint with `ruff` before PRs.

## Testing Guidelines
- No tests are included yet. If adding tests:
  - Use `pytest`; place tests under `tests/` with names like `test_outline.py`.
  - Prefer fast unit tests for `outline` and `slide_builder` logic; mock LLM calls.
  - Run with `pytest -q` and keep coverage reasonable for changed code.

## Commit & PR Guidelines
- Commits: write clear, imperative messages; prefer Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`).
- PRs: include a concise description, rationale, screenshots of UI changes, and steps to reproduce. Link related issues.
- Keep diffs focused; separate refactors from feature changes.
- Ensure app runs locally (`/health` OK) and that generated `.pptx` opens in PowerPoint/Keynote.

## Security & Configuration Tips
- API keys are user-supplied per request and never stored. Do not add server-side keys or log request bodies/keys.
- `llm_router` supports OpenAI-compatible `base_url`; validate inputs and handle errors without leaking secrets.
- Avoid committing sample keys; use `.gitignore` for local env files.
