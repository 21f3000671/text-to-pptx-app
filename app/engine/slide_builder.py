
from typing import Dict, Any, List, Tuple
from pptx import Presentation
from pptx.util import Inches
from pptx.enum.text import PP_ALIGN
from io import BytesIO
from .template_assets import extract_template_images, pick_logo_candidate

def _pick_layout(prs: Presentation) -> Tuple[int, int]:
    content_idx = 1
    title_only_idx = 5
    for i, layout in enumerate(prs.slide_layouts):
        name = (layout.name or "").lower()
        if "title and content" in name or "content" in name:
            content_idx = i
        if "title only" in name:
            title_only_idx = i
    return content_idx, title_only_idx

def _set_title(shape, text: str):
    try:
        if hasattr(shape, "text_frame") and shape.text_frame:
            shape.text_frame.clear()
            p = shape.text_frame.paragraphs[0]
            p.text = text
            p.alignment = PP_ALIGN.LEFT
    except Exception:
        pass

def _set_bullets_textbox(slide, bullets: List[str]):
    tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), slide.width - Inches(2.0), slide.height - Inches(3.0))
    tf = tb.text_frame
    tf.clear()
    for i, b in enumerate(bullets):
        p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
        p.text = b
        p.level = 0

def _set_bullets_placeholder(placeholder, bullets: List[str]) -> bool:
    if not getattr(placeholder, "has_text_frame", False):
        return False
    tf = placeholder.text_frame
    tf.clear()
    for i, b in enumerate(bullets):
        p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
        p.text = b
        p.level = 0
    return True

def _add_logo_if_any(slide, logo_bytes: bytes):
    if not logo_bytes:
        return
    try:
        slide.shapes.add_picture(BytesIO(logo_bytes), slide.width - Inches(1.6), Inches(0.2), width=Inches(1.2))
    except Exception:
        pass

def build_presentation_from_outline(template_path: str, outline: Dict[str, Any], output_path: str):
    prs = Presentation(template_path)
    content_idx, _ = _pick_layout(prs)

    images = extract_template_images(prs)
    logo_bytes = pick_logo_candidate(images)

    if outline.get("title"):
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        if getattr(slide.shapes, "title", None):
            _set_title(slide.shapes.title, str(outline["title"])[:180])
        _add_logo_if_any(slide, logo_bytes)

    for s in outline.get("slides", []):
        layout = prs.slides[0].slide_layout if prs.slides else prs.slide_layouts[content_idx]
        layout = prs.slide_layouts[content_idx]
        slide = prs.slides.add_slide(layout)

        if getattr(slide.shapes, "title", None):
            _set_title(slide.shapes.title, (s.get("title") or "Slide")[:180])

        bullets = [str(b) for b in s.get("bullets", [])][:12]
        body_set = False
        for ph in slide.placeholders:
            try:
                idx = getattr(getattr(ph, "placeholder_format", None), "idx", None)
                if idx == 0:
                    continue
                if _set_bullets_placeholder(ph, bullets):
                    body_set = True
                    break
            except Exception:
                continue
        if not body_set:
            _set_bullets_textbox(slide, bullets)

        if "notes" in s:
            notes = s.get("notes") or ""
            notes_slide = slide.notes_slide
            notes_tf = notes_slide.notes_text_frame
            notes_tf.clear()
            notes_tf.text = notes[:2000]

        _add_logo_if_any(slide, logo_bytes)

    prs.save(output_path)
