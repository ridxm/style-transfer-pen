"""Convert styled polylines into GRBL 0.9 G-code for the AX5 plotter."""
from __future__ import annotations

from typing import Iterable, List

import config
from src.style_applicator import StyledStroke


def _header() -> List[str]:
    return [
        "G21",                  # mm
        "G90",                  # absolute
        config.PEN_UP_CMD,      # make sure pen is up at start
        f"G0 F{config.PLOTTER_FEED_TRAVEL}",
    ]


def _footer() -> List[str]:
    return [
        config.PEN_UP_CMD,
        "G0 X0 Y0",
        "M2",
    ]


def strokes_to_gcode(strokes: Iterable[StyledStroke]) -> str:
    lines: List[str] = _header()
    for stroke in strokes:
        if len(stroke.points) < 2:
            continue
        x0, y0 = stroke.points[0]
        lines.append(f"G0 X{x0:.3f} Y{y0:.3f} F{config.PLOTTER_FEED_TRAVEL}")
        lines.append(config.PEN_DOWN_CMD)
        lines.append(f"G1 F{stroke.feedrate:.0f}")
        for (x, y) in stroke.points[1:]:
            lines.append(f"G1 X{x:.3f} Y{y:.3f}")
        lines.append(config.PEN_UP_CMD)
    lines.extend(_footer())
    return "\n".join(lines) + "\n"
