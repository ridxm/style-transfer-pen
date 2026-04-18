"""Post-process an SVG so its geometry carries the user's style.

Current operations:
- Flatten each <path> to a polyline via svgpathtools.
- Inject per-vertex jitter whose amplitude scales with jerkiness.
- Tag each polyline with a suggested feedrate derived from speed_variance and
  corner_behavior; the gcode_converter reads these hints.
- Reorder strokes to loosely match direction_bias (left-to-right vs. top-down).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from svgpathtools import parse_path, svg2paths2

import config

Point = Tuple[float, float]


@dataclass
class StyledStroke:
    points: List[Point]
    feedrate: float


def _sample_path(path, step_mm: float = 0.5) -> List[Point]:
    length = path.length(error=1e-3)
    if length == 0:
        return []
    n = max(2, int(length / step_mm))
    return [(p.real, p.imag) for p in (path.point(i / (n - 1)) for i in range(n))]


def _apply_jitter(points: List[Point], amplitude: float, rng: random.Random) -> List[Point]:
    if amplitude <= 0 or len(points) < 2:
        return points
    out: List[Point] = []
    for (x, y) in points:
        out.append((x + rng.uniform(-amplitude, amplitude),
                    y + rng.uniform(-amplitude, amplitude)))
    return out


def _feedrate_for(style: Dict[str, float]) -> float:
    base = config.PLOTTER_FEED_DRAW
    # Higher speed_variance -> more feedrate variation handled per-segment later;
    # here we set a baseline scaled by corner_behavior (slower at corners -> slower base).
    scale = max(0.4, min(1.5, style.get("corner_behavior", 1.0)))
    return base * scale


def _sort_strokes(strokes: List[StyledStroke], direction_bias: float) -> List[StyledStroke]:
    if abs(direction_bias) < 1e-3:
        return strokes
    if direction_bias > 0:
        return sorted(strokes, key=lambda s: s.points[0][0] if s.points else 0)
    return sorted(strokes, key=lambda s: s.points[0][1] if s.points else 0)


def apply_style(svg_text: str, style: Dict[str, float],
                seed: int = 0) -> List[StyledStroke]:
    """Parse SVG and return style-perturbed polylines ready for G-code."""
    from io import StringIO
    paths, _attrs, _svg_attrs = svg2paths2(StringIO(svg_text))
    rng = random.Random(seed)

    jitter_amp_mm = 0.3 * float(style.get("jerkiness", 0.0))
    jitter_amp_mm = float(np.clip(jitter_amp_mm, 0.0, 1.5))
    base_feed = _feedrate_for(style)

    strokes: List[StyledStroke] = []
    for path in paths:
        for sub in path.continuous_subpaths():
            pts = _sample_path(sub)
            pts = _apply_jitter(pts, jitter_amp_mm, rng)
            if len(pts) >= 2:
                strokes.append(StyledStroke(points=pts, feedrate=base_feed))

    return _sort_strokes(strokes, float(style.get("direction_bias", 0.0)))
