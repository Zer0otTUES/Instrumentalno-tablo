# Motorcycle Dashboard Simulation

Pygame motorcycle dashboard simulation with a custom instrument-cluster UI and live traffic speed-sign detection through Ultralytics YOLO.

The main dashboard is:

```powershell
python dashboard_exact.py
```

It uses the custom background in `assets/dashboard_bg.png`, overlays speed/RPM/gear/blinkers/warning/blind-spot indicators, and can run YOLO detection from a webcam.

## Features

- Custom full-screen dashboard skin with animated overlays
- Speed, RPM bar, gear display, clock, warning triangle, blinkers, and blind-spot alerts
- Manual keyboard simulation controls
- Optional live camera traffic-sign detection
- YOLO model path configured from `dashboard/config.py`

## Current Model

The dashboard is configured to use this local model:

```text
D:\diplomna_datasets\training_runs\speed_only_FULL_yolov8s_960-2\weights\best.pt
```

This model is intentionally not stored in GitHub. Keep trained models, datasets, and training outputs locally because they are large generated artifacts.

The relevant config values are in `dashboard/config.py`:

```python
DEFAULT_MODEL_PATH = Path(r"D:\diplomna_datasets\training_runs\speed_only_FULL_yolov8s_960-2\weights\best.pt")
YOLO_CONFIDENCE = 0.20
YOLO_IMAGE_SIZE = 960
```

You can still override the model at runtime:

```powershell
python dashboard_exact.py --model "D:\path\to\best.pt"
```

## Requirements

- Python 3.10 or newer
- `pygame`
- `opencv-python`
- `ultralytics`

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pygame opencv-python ultralytics
```

## Run The Dashboard

Run with camera and YOLO enabled:

```powershell
python dashboard_exact.py --scale 0.75
```

Run UI simulation only, without camera:

```powershell
python dashboard_exact.py --no-camera --scale 0.75
```

Use a specific camera index:

```powershell
python dashboard_exact.py --camera 1 --scale 0.75
```

## Controls

```text
Up / Down     Change RPM
Left / Right  Change speed
A / D         Left/right blinkers
W             Warning triangle
Q / E         Left/right blind-spot alert
1..7          Manual speed signs
8             Hump sign
9             Stop sign
0             Scan/no sign
Esc           Exit
```

## Project Structure

```text
dashboard_exact.py          Custom dashboard simulation entry point
assets/dashboard_bg.png     Dashboard background image
dashboard/
  config.py                 Model path, camera, YOLO, and dashboard constants
  core/                     State, drivetrain, blink, blind-spot, detection logic
  ui/                       Older modular dashboard UI components
test_camera.py              Camera sanity-check script
yolo_webcam.py              Standalone YOLO webcam test script
```

## Repository Hygiene

GitHub should contain the source code and small UI assets only. These are kept local and ignored:

- trained model weights: `*.pt`
- training outputs: `runs/`
- datasets: `datasets/`
- Python caches and virtual environments

If a fresh clone needs the model, place or update the model path in `dashboard/config.py`, or pass `--model` when running `dashboard_exact.py`.

## Notes

- `dashboard_exact.py` is the current polished UI.
- `dashboard/main.py` is the older dashboard entry point.
- The dashboard can run without YOLO using `--no-camera`, which is useful for UI testing.
