
# Text → PowerPoint (Template-Aware)

Turn bulk text or markdown into a fully styled PowerPoint using **your** `.pptx/.potx` template. Keys are never stored. Open-source (MIT).

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
# open http://localhost:8000
```
