"""Receive IMU + pressure stream from the Arduino Nano 33 BLE Sense pen.

Packet format (little-endian, 30 bytes):
    float32 t_ms, ax, ay, az, gx, gy, gz, pressure
Notifications arrive at ~100 Hz.
"""
from __future__ import annotations

import asyncio
import struct
import time
from dataclasses import dataclass
from typing import AsyncIterator, Callable, Optional

from bleak import BleakClient, BleakScanner

import config

PACKET_FMT = "<ffffffff"
PACKET_SIZE = struct.calcsize(PACKET_FMT)


@dataclass
class PenSample:
    t: float          # host-side timestamp (seconds, monotonic)
    t_dev_ms: float   # device timestamp (ms since boot)
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float
    pressure: float


class BLEReceiver:
    def __init__(self, name: str = config.PEN_BLE_NAME,
                 char_uuid: str = config.PEN_CHAR_UUID):
        self.name = name
        self.char_uuid = char_uuid
        self._client: Optional[BleakClient] = None
        self._queue: asyncio.Queue[PenSample] = asyncio.Queue()

    async def _find_device(self):
        devices = await BleakScanner.discover(timeout=5.0)
        for d in devices:
            if d.name and self.name in d.name:
                return d
        raise RuntimeError(f"Pen '{self.name}' not found over BLE")

    def _on_notify(self, _handle, data: bytearray):
        if len(data) < PACKET_SIZE:
            return
        t_dev_ms, ax, ay, az, gx, gy, gz, pressure = struct.unpack(
            PACKET_FMT, bytes(data[:PACKET_SIZE])
        )
        sample = PenSample(time.monotonic(), t_dev_ms, ax, ay, az, gx, gy, gz, pressure)
        self._queue.put_nowait(sample)

    async def connect(self):
        device = await self._find_device()
        self._client = BleakClient(device)
        await self._client.connect()
        await self._client.start_notify(self.char_uuid, self._on_notify)

    async def disconnect(self):
        if self._client and self._client.is_connected:
            await self._client.stop_notify(self.char_uuid)
            await self._client.disconnect()

    async def stream(self) -> AsyncIterator[PenSample]:
        while True:
            yield await self._queue.get()


async def record(duration_s: float, on_sample: Callable[[PenSample], None]) -> None:
    rx = BLEReceiver()
    await rx.connect()
    try:
        deadline = time.monotonic() + duration_s
        async for s in rx.stream():
            on_sample(s)
            if time.monotonic() >= deadline:
                break
    finally:
        await rx.disconnect()
