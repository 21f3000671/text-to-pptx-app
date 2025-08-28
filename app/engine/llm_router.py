
from typing import List, Dict, Any, Optional
import json, re
import litellm

litellm.drop_params = True

def _normalize_model(provider: str, model: str, base_url: Optional[str]) -> str:
    if base_url:
        return model
    prov = (provider or "").lower().strip()
    if "/" in model:
        return model
    if prov == "anthropic":
        return f"anthropic/{model}"
    if prov in ("gemini", "google"):
        return f"gemini/{model}"
    return model

def chat_json(
    provider: str,
    model: str,
    api_key: str,
    messages: List[Dict[str, Any]],
    base_url: Optional[str] = None,
    max_output_tokens: int = 2000,
    temperature: float = 0.2,
) -> Dict[str, Any]:
    use_model = _normalize_model(provider, model, base_url)
    kwargs: Dict[str, Any] = {
        "model": use_model,
        "messages": messages,
        "api_key": api_key,
        "temperature": temperature,
        "max_tokens": max_output_tokens,
        "response_format": {"type": "json_object"},
    }
    if base_url:
        kwargs["api_base"] = base_url

    resp = litellm.completion(**kwargs)
    content_chunks = []
    for choice in resp.get("choices", []):
        msg = choice.get("message", {})
        if isinstance(msg.get("content"), list):
            for part in msg["content"]:
                if isinstance(part, dict) and part.get("type") in ("text", "output_text"):
                    content_chunks.append(part.get("text", "") or part.get("output_text", ""))
        else:
            content_chunks.append(msg.get("content", ""))
    text = "\n".join([c for c in content_chunks if c])

    try:
        data = json.loads(text)
    except Exception as e1:
        # Try to extract JSON from text using regex
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise ValueError(f"Model did not return JSON. Got: {text[:300]}...")
        try:
            data = json.loads(m.group(0))
        except Exception as e2:
            # If regex extraction also fails, raise the original error with more context
            raise ValueError(f"Failed to parse JSON. Original error: {e1}. Regex extraction error: {e2}. Text: {text[:500]}...")
    return data
