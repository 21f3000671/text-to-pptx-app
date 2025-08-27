
from typing import Dict, Any, Optional, List
import re
from .llm_router import chat_json

SYSTEM_PROMPT = """You turn long text or markdown into slide outlines for PowerPoint.
Return STRICT JSON with this schema:
{
  "title": "string (overall deck title)",
  "slides": [
    {
      "title": "string",
      "bullets": ["string", "..."],
      "notes": "optional speaker notes string"
    }
  ]
}
Rules:
- Keep bullets concise (max ~12 words each).
- Prefer 4–6 bullets per slide.
- Produce at most {max_slides} slides.
- If the input already has clear markdown headings, reuse those as slide titles.
- Never include markdown formatting marks in the JSON text.
- If guidance hints a style (e.g., investor pitch), adapt slide ordering and titles accordingly.
"""

def _fallback_outline(text: str, max_slides: int) -> Dict[str, Any]:
    lines = text.splitlines()
    slides = []
    current = {"title": None, "bullets": []}
    def flush():
        if current["title"] or current["bullets"]:
            slides.append({"title": current["title"] or "Slide", "bullets": current["bullets"][:8]})
    for line in lines:
        if re.match(r"^\s{0,3}#{1,6}\s+", line):
            if len(slides) >= max_slides:
                break
            flush()
            import re as _re
            title = _re.sub(r"^\s*#+\s+", "", line).strip()
            current = {"title": title[:120], "bullets": []}
        elif re.match(r"^\s*[-*+]\s+", line):
            bullet = re.sub(r"^\s*[-*+]\s+", "", line).strip()
            if bullet:
                current["bullets"].append(bullet[:160])
        elif line.strip():
            sentence = line.strip()
            if len(sentence) > 180:
                chunks = re.split(r"(?<=[.!?])\s+", sentence)
                for c in chunks:
                    c = c.strip()
                    if c:
                        current["bullets"].append(c[:160])
            else:
                current["bullets"].append(sentence[:160])
    flush()
    if not slides:
        paras = [p.strip() for p in text.split("\\n\\n") if p.strip()]
        for p in paras[:max_slides]:
            slides.append({"title": p.split(".")[0][:80] if "." in p else "Slide", "bullets": [p[:160]]})
    title = slides[0]["title"] if slides else "Presentation"
    return {"title": title, "slides": slides[:max_slides]}

def _normalize_outline(data: Any, max_slides: int, include_notes: bool) -> Dict[str, Any]:
    if not isinstance(data, dict):
        data = {}
    title = data.get("title") if isinstance(data.get("title"), str) else None
    slides_in = data.get("slides")
    slides_out: List[Dict[str, Any]] = []
    if isinstance(slides_in, list):
        for raw in slides_in:
            if not isinstance(raw, dict):
                continue
            st = raw.get("title")
            bl = raw.get("bullets")
            nt = raw.get("notes")
            title_s = st if isinstance(st, str) and st.strip() else "Slide"
            bullets_s = [str(b) for b in (bl or []) if isinstance(b, (str, int, float))]
            bullets_s = [b[:200] for b in bullets_s][:12]
            item: Dict[str, Any] = {"title": title_s, "bullets": bullets_s}
            if include_notes:
                item["notes"] = nt if isinstance(nt, str) else ""
            slides_out.append(item)
    if not slides_out:
        slides_out = [{"title": "Overview", "bullets": ["Summary point 1", "Summary point 2"]}]
        if include_notes:
            slides_out[0]["notes"] = ""
    slides_out = slides_out[:max_slides]
    if not title:
        title = slides_out[0]["title"] if slides_out else "Presentation"
    return {"title": title, "slides": slides_out}

async def build_outline_from_text(
    text: str,
    guidance: str,
    provider: str,
    model: str,
    api_key: str,
    base_url: Optional[str],
    target_slide_count: int,
    include_notes: bool = False,
) -> Dict[str, Any]:
    has_headings = bool(re.search(r"^\s{0,3}#{1,6}\s+", text, re.M))
    if (not guidance and has_headings) or (not api_key):
        base = _fallback_outline(text, target_slide_count)
        if include_notes:
            for s in base["slides"]:
                s["notes"] = ""
        return base

    prompt = SYSTEM_PROMPT.format(max_slides=target_slide_count)
    user = f"Input Text:\\n{text}\\n\\nGuidance (optional): {guidance or 'none'}\\nRespond with STRICT JSON only."
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user},
    ]

    try:
        data = chat_json(
            provider=provider,
            model=model,
            api_key=api_key,
            messages=messages,
            base_url=base_url,
            max_output_tokens=4000 if include_notes else 2000,
            temperature=0.2,
        )
        data = _normalize_outline(data, target_slide_count, include_notes)
    except Exception:
        data = _fallback_outline(text, target_slide_count)
        if include_notes:
            for s in data.get("slides", []):
                s.setdefault("notes", "")
    if not data.get("slides"):
        data = _fallback_outline(text, target_slide_count)
        if include_notes:
            for s in data.get("slides", []):
                s.setdefault("notes", "")
    if "title" not in data:
        data["title"] = data["slides"][0]["title"] if data.get("slides") else "Presentation"
    return data
