"""Stream G-code to a GRBL 0.9 plotter over USB serial.

Uses simple send-response handshake: one line sent, wait for 'ok' or 'error'.
"""
from __future__ import annotations

import time
from typing import Iterable, Optional

import serial

import config


class PlotterController:
    def __init__(self, port: str = config.PLOTTER_PORT,
                 baud: int = config.PLOTTER_BAUD):
        self.ser = serial.Serial(port, baud, timeout=2)
        time.sleep(2)            # Arduino-style reset delay
        self.ser.reset_input_buffer()

    def _send_line(self, line: str) -> str:
        self.ser.write((line.strip() + "\n").encode("ascii"))
        resp = b""
        while True:
            chunk = self.ser.readline()
            if not chunk:
                break
            resp += chunk
            low = chunk.lower()
            if b"ok" in low or b"error" in low:
                break
        return resp.decode("ascii", errors="replace").strip()

    def wake(self) -> None:
        self.ser.write(b"\r\n\r\n")
        time.sleep(2)
        self.ser.reset_input_buffer()

    def home(self) -> None:
        self._send_line("$H")

    def run(self, gcode: str, on_progress: Optional[callable] = None) -> None:
        lines = [ln for ln in gcode.splitlines() if ln.strip() and not ln.startswith(";")]
        for i, line in enumerate(lines):
            resp = self._send_line(line)
            if on_progress:
                on_progress(i + 1, len(lines), line, resp)
            if "error" in resp.lower():
                raise RuntimeError(f"GRBL error on '{line}': {resp}")

    def close(self) -> None:
        if self.ser.is_open:
            self.ser.close()


def send_file(path: str) -> None:
    with open(path) as f:
        gcode = f.read()
    plotter = PlotterController()
    plotter.wake()
    try:
        plotter.run(gcode)
    finally:
        plotter.close()
