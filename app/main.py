
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask
from typing import Optional
import uvicorn
import os, tempfile, math
from app.engine.outline import build_outline_from_text
from app.engine.slide_builder import build_presentation_from_outline

APP_NAME = "Text→PPTX (Template Aware)"
app = FastAPI(title=APP_NAME)

# Static & templates
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_name": APP_NAME})

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/generate")
async def generate(
    request: Request,
    text: str = Form(...),
    guidance: Optional[str] = Form(None),
    provider: str = Form("openai"),
    model: str = Form("gpt-4o-mini"),
    api_key: str = Form(...),
    base_url: Optional[str] = Form(None),
    generate_notes: Optional[bool] = Form(False),
    template_file: UploadFile = File(...),
):
    name = template_file.filename or ""
    if not name.lower().endswith((".pptx", ".potx")):
        raise HTTPException(status_code=400, detail="Please upload a .pptx or .potx file.")

    tmp_dir = tempfile.mkdtemp(prefix="pptxgen_")
    template_path = os.path.join(tmp_dir, name)
    with open(template_path, "wb") as f:
        f.write(await template_file.read())

    char_count = len(text or "")
    target = max(5, min(30, int(math.ceil(char_count / 800.0)) + 1))

    try:
        outline = await build_outline_from_text(
            text=text,
            guidance=guidance or "",
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            target_slide_count=target,
            include_notes=bool(generate_notes),
        )
    except Exception as e:
        print("Outline generation error (falling back):", repr(e))
        from app.engine.outline import _fallback_outline
        outline = _fallback_outline(text, target)

    output_path = os.path.join(tmp_dir, "generated.pptx")
    try:
        build_presentation_from_outline(template_path, outline, output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PowerPoint build failed: {str(e)}")

    def _cleanup():
        try:
            if os.path.exists(tmp_dir):
                for root, dirs, files in os.walk(tmp_dir, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for d in dirs:
                        os.rmdir(os.path.join(root, d))
                os.rmdir(tmp_dir)
        except Exception:
            pass

    return FileResponse(
        output_path,
        filename="generated.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        background=BackgroundTask(_cleanup)
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
