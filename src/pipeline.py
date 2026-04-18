"""End-to-end orchestration: capture -> style -> generate -> plot."""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np

import config
from src.ble_receiver import BLEReceiver, PenSample
from src.camera_tracker import CameraTracker, TipSample
from src.data_fusion import fuse
from src.gcode_converter import strokes_to_gcode
from src.plotter_controller import PlotterController
from src.style_applicator import apply_style
from src.style_extractor import extract
from src.svg_generator import generate_svg


@dataclass
class CaptureResult:
    pen_samples: List[PenSample]
    tip_samples: List[TipSample]
    fused: np.ndarray


async def capture(duration_s: float) -> CaptureResult:
    pen: List[PenSample] = []
    tip: List[TipSample] = []

    rx = BLEReceiver()
    cam = CameraTracker()
    await rx.connect()

    stop = time.monotonic() + duration_s

    async def pull_pen():
        async for s in rx.stream():
            pen.append(s)
            if time.monotonic() >= stop:
                return

    async def pull_cam():
        loop = asyncio.get_running_loop()
        def producer():
            for s in cam.stream():
                tip.append(s)
                if time.monotonic() >= stop:
                    return
        await loop.run_in_executor(None, producer)

    try:
        await asyncio.gather(pull_pen(), pull_cam())
    finally:
        await rx.disconnect()
        cam.release()

    return CaptureResult(pen, tip, fuse(pen, tip))


def run(prompt: str, duration_s: float = 15.0, plot: bool = True) -> Path:
    """Capture a sample drawing, extract style, generate and plot a new drawing."""
    capture_result = asyncio.run(capture(duration_s))
    profile = extract(capture_result.fused).as_dict()

    svg = generate_svg(prompt, profile)
    strokes = apply_style(svg, profile)
    gcode = strokes_to_gcode(strokes)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_svg = config.OUTPUTS_DIR / f"{stamp}.svg"
    out_gcode = config.OUTPUTS_DIR / f"{stamp}.gcode"
    out_profile = config.OUTPUTS_DIR / f"{stamp}.style.json"
    out_svg.write_text(svg)
    out_gcode.write_text(gcode)
    out_profile.write_text(json.dumps(profile, indent=2))

    if plot:
        plotter = PlotterController()
        plotter.wake()
        try:
            plotter.run(gcode)
        finally:
            plotter.close()

    return out_gcode
