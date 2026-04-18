"""Reduce a fused sample stream to a compact style feature vector.

Style profile keys:
    pressure_mean, pressure_std
    speed_mean, speed_variance
    jerkiness                      (RMS of d(accel)/dt normalized by speed_mean)
    curvature_pressure_correlation (Pearson r between |curvature| and pressure)
    stroke_rhythm                  (mean stroke duration / std, from pressure gating)
    direction_bias                 (mean signed heading change, rad)
    corner_behavior                (ratio of slow-down at high-curvature points)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict

import numpy as np


@dataclass
class StyleProfile:
    pressure_mean: float
    pressure_std: float
    speed_mean: float
    speed_variance: float
    jerkiness: float
    curvature_pressure_correlation: float
    stroke_rhythm: float
    direction_bias: float
    corner_behavior: float

    def as_dict(self) -> Dict[str, float]:
        return {k: float(v) for k, v in asdict(self).items()}


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 2 or b.size < 2:
        return 0.0
    sa, sb = a.std(), b.std()
    if sa == 0 or sb == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def _curvature(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    dx = np.gradient(x)
    dy = np.gradient(y)
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)
    denom = np.power(dx * dx + dy * dy, 1.5) + 1e-9
    return (dx * ddy - dy * ddx) / denom


def _strokes(pressure: np.ndarray, threshold: float) -> list[tuple[int, int]]:
    down = pressure > threshold
    strokes = []
    start = None
    for i, d in enumerate(down):
        if d and start is None:
            start = i
        elif not d and start is not None:
            strokes.append((start, i))
            start = None
    if start is not None:
        strokes.append((start, len(down)))
    return strokes


def extract(fused: np.ndarray) -> StyleProfile:
    if fused.size < 5:
        return StyleProfile(0, 0, 0, 0, 0, 0, 0, 0, 0)

    t = fused["t"].astype(np.float64)
    dt = np.diff(t, prepend=t[0])
    dt[dt <= 0] = 1e-3

    pressure = fused["pressure"].astype(np.float64)
    speed = fused["speed"].astype(np.float64)
    accel = fused["accel"].astype(np.float64)

    pressure_mean = pressure.mean()
    pressure_std = pressure.std()
    speed_mean = speed.mean()
    speed_variance = float(speed.var())

    jerk = np.gradient(accel) / dt
    jerkiness = float(np.sqrt(np.mean(jerk ** 2)) / (speed_mean + 1e-6))

    curv = np.abs(_curvature(fused["x"].astype(np.float64), fused["y"].astype(np.float64)))
    curvature_pressure_correlation = _safe_corr(curv, pressure)

    thresh = pressure_mean + 0.25 * pressure_std
    strokes = _strokes(pressure, thresh)
    if len(strokes) >= 2:
        durations = np.array([(t[e - 1] - t[s]) for s, e in strokes])
        stroke_rhythm = float(durations.mean() / (durations.std() + 1e-6))
    else:
        stroke_rhythm = 0.0

    heading = np.arctan2(np.gradient(fused["y"].astype(np.float64)),
                         np.gradient(fused["x"].astype(np.float64)))
    dh = np.diff(np.unwrap(heading))
    direction_bias = float(dh.mean()) if dh.size else 0.0

    if curv.size:
        top = curv > np.quantile(curv, 0.9)
        if top.any():
            corner_behavior = float(speed[top].mean() / (speed_mean + 1e-6))
        else:
            corner_behavior = 1.0
    else:
        corner_behavior = 1.0

    return StyleProfile(
        pressure_mean=pressure_mean,
        pressure_std=pressure_std,
        speed_mean=speed_mean,
        speed_variance=speed_variance,
        jerkiness=jerkiness,
        curvature_pressure_correlation=curvature_pressure_correlation,
        stroke_rhythm=stroke_rhythm,
        direction_bias=direction_bias,
        corner_behavior=corner_behavior,
    )
