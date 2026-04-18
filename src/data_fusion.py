"""Align pen (BLE) and paper (camera) streams by timestamp.

Output is a structured numpy array, one row per fused sample at camera rate.
IMU values are linearly interpolated to camera timestamps; velocity/accel are
derived from the interpolated position trajectory.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

from src.ble_receiver import PenSample
from src.camera_tracker import TipSample

FUSED_DTYPE = np.dtype([
    ("t", "f8"),
    ("x", "f4"), ("y", "f4"),
    ("pressure", "f4"),
    ("speed", "f4"), ("accel", "f4"),
    ("gx", "f4"), ("gy", "f4"), ("gz", "f4"),
])


def _interp(t_target: np.ndarray, t_src: np.ndarray, v_src: np.ndarray) -> np.ndarray:
    if len(t_src) == 0:
        return np.zeros_like(t_target)
    return np.interp(t_target, t_src, v_src)


def fuse(pen: Sequence[PenSample], tip: Sequence[TipSample]) -> np.ndarray:
    if not tip:
        return np.zeros(0, dtype=FUSED_DTYPE)

    t_cam = np.array([s.t for s in tip], dtype=np.float64)
    x = np.array([s.x_mm for s in tip], dtype=np.float32)
    y = np.array([s.y_mm for s in tip], dtype=np.float32)

    t_pen = np.array([s.t for s in pen], dtype=np.float64)
    pressure = np.array([s.pressure for s in pen], dtype=np.float32)
    gx = np.array([s.gx for s in pen], dtype=np.float32)
    gy = np.array([s.gy for s in pen], dtype=np.float32)
    gz = np.array([s.gz for s in pen], dtype=np.float32)

    p_i = _interp(t_cam, t_pen, pressure)
    gx_i = _interp(t_cam, t_pen, gx)
    gy_i = _interp(t_cam, t_pen, gy)
    gz_i = _interp(t_cam, t_pen, gz)

    dt = np.diff(t_cam, prepend=t_cam[0])
    dt[dt <= 0] = 1e-3
    vx = np.gradient(x) / dt
    vy = np.gradient(y) / dt
    speed = np.hypot(vx, vy).astype(np.float32)
    accel = np.gradient(speed).astype(np.float32) / dt

    out = np.zeros(len(t_cam), dtype=FUSED_DTYPE)
    out["t"] = t_cam
    out["x"] = x
    out["y"] = y
    out["pressure"] = p_i
    out["speed"] = speed
    out["accel"] = accel.astype(np.float32)
    out["gx"] = gx_i
    out["gy"] = gy_i
    out["gz"] = gz_i
    return out
