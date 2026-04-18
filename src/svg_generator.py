"""Call OpenAI to generate an SVG drawing matching a prompt + style profile."""
from __future__ import annotations

import re
from typing import Dict

from openai import OpenAI

import config

_SVG_RE = re.compile(r"<svg[\s\S]*?</svg>", re.IGNORECASE)


SYSTEM_PROMPT = """You are a minimalist line-art illustrator that outputs a single valid SVG.
Constraints:
- Output ONLY one <svg>...</svg> element, no prose, no markdown fences.
- viewBox must be "0 0 {w} {h}" (millimeters) and width/height must match.
- Use only <path> elements with fill="none" and stroke="black".
- Produce clean, continuous strokes suitable for a pen plotter (no fills, no text).
- Keep total path count under 60.
"""


def _style_hint(style: Dict[str, float]) -> str:
    parts = [f"{k}={v:.3f}" for k, v in style.items()]
    return (
        "The drawing will be redrawn by a plotter in the style described by this profile:\n"
        + ", ".join(parts)
        + ". Bias line weight suggestions and stroke count to suit these characteristics."
    )


def generate_svg(prompt: str, style: Dict[str, float],
                 width_mm: float = config.PAPER_WIDTH_MM,
                 height_mm: float = config.PAPER_HEIGHT_MM,
                 model: str = config.OPENAI_MODEL) -> str:
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    system = SYSTEM_PROMPT.format(w=width_mm, h=height_mm)
    user = f"Draw: {prompt}\n\n{_style_hint(style)}"
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0.8,
    )
    text = resp.choices[0].message.content or ""
    match = _SVG_RE.search(text)
    if not match:
        raise ValueError(f"No SVG found in model response: {text[:200]}")
    return match.group(0)
