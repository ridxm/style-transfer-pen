# penDNA — Style Transfer Drawing Pen

An instrumented pen learns *how* you draw, then a plotter draws *what you ask for* in your style.

- **Pen (Arduino Nano 33 BLE Sense Rev2)** streams IMU + tip-pressure at 100 Hz over BLE.
- **Webcam (Logitech Brio 105)** tracks the pen tip on paper via OpenCV.
- **Raspberry Pi 5** fuses both streams, extracts a style profile, asks OpenAI for an SVG matching a prompt, perturbs the SVG with the user's style, converts it to G-code, and streams it to a **Doesbot AX5** plotter running GRBL 0.9.

## Pipeline

```
 pen IMU + pressure (BLE)  ─┐
                            ├─> data_fusion ─> style_extractor ─┐
 webcam pen-tip path ───────┘                                   │
                                                                ▼
                 prompt ─────────────────────> svg_generator (OpenAI)
                                                                │
                                                                ▼
                                            style_applicator (jitter, feedrate, ordering)
                                                                │
                                                                ▼
                                                        gcode_converter
                                                                │
                                                                ▼
                                                      plotter_controller ─> AX5
```

## Repository layout

```
arduino/pen_firmware.ino     Nano 33 BLE firmware (BMI270 + FSR on A0)
src/ble_receiver.py          BLE client, parses 32-byte packets
src/camera_tracker.py        HSV tip detection, pixels -> mm on paper
src/data_fusion.py           Time-align pen and camera into a numpy record array
src/style_extractor.py       9-feature style profile
src/svg_generator.py         OpenAI call, returns a single <svg>
src/style_applicator.py      Flatten paths, inject style-driven perturbation
src/gcode_converter.py       Polylines -> GRBL G-code (M3/M5 pen control)
src/plotter_controller.py    pyserial send-response streaming
src/pipeline.py              End-to-end orchestrator
src/demo_server.py           Flask UI
config.py                    Central settings, reads env vars
requirements.txt
.env.example
```

## Setup on the Pi

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in OPENAI_API_KEY, serial port, etc.
```

Flash `arduino/pen_firmware.ino` to the Nano 33 BLE Sense Rev2 with the
Mbed OS Nano core and the `Arduino_BMI270_BMM150` + `ArduinoBLE` libraries.

## Running

```bash
# export env vars, then:
python -m src.demo_server
# open http://<pi>:5000 and press Go after drawing for ~15 s
```

Or headless:

```python
from src import pipeline
pipeline.run("a small house with a tree", duration_s=15.0, plot=True)
```

## Style features

| feature | meaning |
| --- | --- |
| `pressure_mean`, `pressure_std` | how hard / variable you press |
| `speed_mean`, `speed_variance` | pace and variability |
| `jerkiness` | high-frequency content in acceleration (drives path jitter) |
| `curvature_pressure_correlation` | do you press harder in corners? |
| `stroke_rhythm` | mean/std of pen-down durations |
| `direction_bias` | left-to-right vs top-to-bottom tendency (drives stroke order) |
| `corner_behavior` | how much you slow down at high-curvature points |

## Calibration notes

- `PAPER_ROI` in `config.py` must match the paper in the camera frame.
- Tune `PEN_TIP_HSV_LOW/HIGH` to the marker color on your pen tip.
- `PLOTTER_PORT` is usually `/dev/ttyUSB0` on the Pi; check `dmesg` after plugging in.

## Hardware

- Arduino Nano 33 BLE Sense Rev2 (BMI270 IMU)
- FSR thin-film sensor + 10 kΩ divider -> A0
- 3.7 V LiPo through the Nano's VIN
- Logitech Brio 105 (USB, overhead)
- Doesbot AX5 CoreXY pen plotter, GRBL 0.9, A5 area
- Raspberry Pi 5 4 GB

## License

TBD.
