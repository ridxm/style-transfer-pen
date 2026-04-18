"""Extract pen tip position on paper from the overhead webcam.

Uses HSV color tracking on a colored marker attached to the pen tip.
Each detection maps pixel coordinates -> mm coordinates on the paper.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterator, Optional

import cv2
import numpy as np

import config


@dataclass
class TipSample:
    t: float          # host monotonic seconds
    x_mm: float
    y_mm: float
    confidence: float


class CameraTracker:
    def __init__(self, camera_index: int = config.CAMERA_INDEX):
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
        self.roi = config.PAPER_ROI
        self.low = np.array(config.PEN_TIP_HSV_LOW, dtype=np.uint8)
        self.high = np.array(config.PEN_TIP_HSV_HIGH, dtype=np.uint8)
        self._px_per_mm_x = self.roi[2] / config.PAPER_WIDTH_MM
        self._px_per_mm_y = self.roi[3] / config.PAPER_HEIGHT_MM

    def _pixel_to_mm(self, px: float, py: float) -> tuple[float, float]:
        x_mm = (px - self.roi[0]) / self._px_per_mm_x
        y_mm = (py - self.roi[1]) / self._px_per_mm_y
        return x_mm, y_mm

    def _detect_tip(self, frame: np.ndarray) -> Optional[tuple[float, float, float]]:
        x, y, w, h = self.roi
        roi = frame[y:y + h, x:x + w]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.low, self.high)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) < 20:
            return None
        m = cv2.moments(c)
        if m["m00"] == 0:
            return None
        cx = m["m10"] / m["m00"] + x
        cy = m["m01"] / m["m00"] + y
        confidence = min(1.0, cv2.contourArea(c) / 500.0)
        return cx, cy, confidence

    def stream(self) -> Iterator[TipSample]:
        while True:
            ok, frame = self.cap.read()
            if not ok:
                continue
            t = time.monotonic()
            det = self._detect_tip(frame)
            if det is None:
                continue
            cx, cy, conf = det
            x_mm, y_mm = self._pixel_to_mm(cx, cy)
            yield TipSample(t, x_mm, y_mm, conf)

    def release(self):
        self.cap.release()
