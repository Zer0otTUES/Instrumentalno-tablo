# trafic-sign-yolo

Traffic sign detection using Ultralytics YOLOv8 and OpenCV. The repo includes a labeled YOLO-format dataset, multiple training runs, and simple webcam inference scripts.

## What is this project?
This project trains and runs a YOLOv8 detector for common traffic signs (9 classes). It ships:
- a dataset in YOLO format (`datasets/traffic-signs`)
- trained weights from past runs (`runs/detect/*/weights/best.pt`)
- a webcam inference script (`yolo_webcam.py`)
- a camera test script (`test_camera.py`)

## Requirements
- Python 3.10 (the included virtual environment uses 3.10.11)
- Packages: `ultralytics`, `opencv-python` (and `torch`, installed as a dependency)

## Setup
If you want a clean environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install ultralytics opencv-python
```

If you already have the provided `.venv`, just activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Quickstart: webcam detection
1) Test the camera:

```powershell
python test_camera.py
```

2) Run YOLO on the webcam:

```powershell
python yolo_webcam.py
```

The default model is set in `yolo_webcam.py`:

```python
MODEL_NAME = "runs/detect/train2/weights/best.pt"
```

Change it to a different weight file as needed (for example `yolov8n.pt` or `runs/detect/train3/weights/best.pt`).

## Code walkthrough (detailed)

### `test_camera.py` (camera sanity check)
What it does: opens the webcam, shows the live feed in a window, and exits when you press `q`.

Step by step:
1) `import cv2` brings in OpenCV, which handles video capture and display.
2) `cap = cv2.VideoCapture(0)` creates a video capture object for camera index 0 (the default camera).
3) `cap.isOpened()` verifies the camera is accessible. If it fails, the script prints a hint and exits early.
4) The `while True` loop continuously reads frames:
   - `ok, frame = cap.read()` returns a boolean and the captured frame.
   - If `ok` is false, it prints an error and stops the loop.
   - `cv2.imshow("Camera Test", frame)` displays the current frame in a window.
   - `cv2.waitKey(1)` checks for key presses; `& 0xFF` isolates the key code; `ord('q')` matches the Q key. If Q is pressed, the loop exits.
5) Cleanup:
   - `cap.release()` frees the camera device.
   - `cv2.destroyAllWindows()` closes any OpenCV windows.

Notes:
- If the camera window opens but pressing `q` does nothing, click the window to focus it.
- If index `0` fails, try `1` or `2`.

### `yolo_webcam.py` (live YOLO traffic sign detection)
What it does: opens the webcam, runs a YOLOv8 model on every frame, draws detections, and shows the annotated video feed.

Step by step:
1) Imports:
   - `from ultralytics import YOLO` loads the Ultralytics YOLOv8 API.
   - `import cv2` provides webcam and display functions.
2) Model selection:
   - `MODEL_NAME = "runs/detect/train2/weights/best.pt"` points to a trained traffic-sign model inside this repo.
   - You can swap this to `yolov8n.pt` (general objects) or another run’s weights.
3) Model loading:
   - `model = YOLO(MODEL_NAME)` loads weights into a YOLOv8 detector.
   - The script prints messages before and after loading for feedback.
4) Webcam setup:
   - `cap = cv2.VideoCapture(0)` opens the default webcam.
   - `cap.isOpened()` ensures it actually opened.
5) Inference loop:
   - `ret, frame = cap.read()` grabs a frame; if it fails, the loop stops.
   - `results = model.predict(frame, conf=0.35, imgsz=640, verbose=False)` runs detection:
     - `frame` is a single image (a NumPy array from OpenCV).
     - `conf=0.35` filters out detections below 0.35 confidence.
     - `imgsz=640` resizes internally for inference.
     - `verbose=False` keeps the console quiet.
   - `results[0]` is the single frame’s result; `results[0].plot()` draws bounding boxes, class labels, and confidence on the image and returns the annotated frame.
   - `cv2.imshow("YOLO Traffic Sign Detection", annotated)` displays the annotated frame.
   - `cv2.waitKey(1)` checks for the `q` key to exit.
6) Cleanup:
   - `cap.release()` releases the camera.
   - `cv2.destroyAllWindows()` closes OpenCV windows.

What the detections mean:
- The class names come from the model weights you load.
- If you use `runs/detect/*/weights/best.pt`, the classes are the 9 traffic sign labels listed in `datasets/traffic-signs/data.yaml`.
- If you switch to `yolov8n.pt`, you will see COCO object classes instead of traffic signs.

Easy tweaks (same code, different behavior):
- Increase `conf` to reduce false positives; lower it to detect more objects.
- Reduce `imgsz` for faster FPS on CPU; increase it for potentially better accuracy.
- Change `MODEL_NAME` to point at a different trained weight file.

## Dataset
Location: `datasets/traffic-signs`

Structure (YOLO format):
- `train/images`, `train/labels`
- `val/images`, `val/labels`
- `test/images`, `test/labels`

Counts (images + label files):
- train: 993
- val: 123
- test: 123

Classes (`datasets/traffic-signs/data.yaml`):
```
0: 20-Speed
1: 30-speed
2: 40-Speed
3: 50-Speed
4: 60-Speed
5: 70-Speed
6: 80-Speed
7: Hump
8: Stop
```

Label format (YOLO):
```
class_id x_center y_center width height
```
All values are normalized to `[0, 1]` relative to image size.

## Training
Training runs were produced with Ultralytics YOLO. Each run folder contains the exact parameters in `args.yaml`.

Example commands that match the recorded runs:

- `runs/detect/train` (recorded 1 epoch; planned 30):
```powershell
yolo detect train data=datasets/traffic-signs/data.yaml model=yolov8n.pt epochs=30 imgsz=640 batch=16 device=cpu
```

- `runs/detect/train2` (recorded 5 epochs):
```powershell
yolo detect train data=datasets/traffic-signs/data.yaml model=yolov8n.pt epochs=5 imgsz=416 batch=8 device=cpu freeze=10
```

- `runs/detect/train3` (recorded 2 epochs; planned 100):
```powershell
yolo detect train data=datasets/traffic-signs/data.yaml model=yolov8s.pt epochs=100 imgsz=640 batch=8 device=cpu cos_lr=true mixup=0.15 degrees=5 shear=2.0
```

Note: the training outputs show fewer epochs recorded than configured, which suggests the runs were stopped early.

## Training results snapshot
Metrics below are from the last recorded epoch of each run (`results.csv`).

| Run | Epoch | Precision | Recall | mAP50 | mAP50-95 |
| --- | ----- | --------- | ------ | ----- | -------- |
| train  | 1 | 0.73878 | 0.06844 | 0.27287 | 0.22318 |
| train2 | 5 | 0.64919 | 0.54129 | 0.61551 | 0.50928 |
| train3 | 2 | 0.63048 | 0.65673 | 0.66817 | 0.47958 |

## Outputs and artifacts
Each training run folder under `runs/detect/` typically contains:
- `args.yaml` (full training config)
- `results.csv` and `results.png`
- `confusion_matrix*.png`, `Box*.png` curves
- `weights/best.pt` and `weights/last.pt`

These are generated by Ultralytics and can be regenerated by rerunning training.

## Troubleshooting
- Camera won’t open: change `cv2.VideoCapture(0)` to `1` or `2` in `test_camera.py` / `yolo_webcam.py`, and close other apps using the camera.
- Slow FPS on CPU: switch to `yolov8n.pt`, lower `imgsz`, or increase the confidence threshold in `model.predict`.
- Missing weights: update `MODEL_NAME` to a path that exists on your machine.

## Project structure (key files)
```
trafic-sign-yolo/
  test_camera.py
  yolo_webcam.py
  yolov8n.pt
  yolov8s.pt
  datasets/traffic-signs/
    data.yaml
    train/
      images/
      labels/
    val/
      images/
      labels/
    test/
      images/
      labels/
  runs/detect/
    train/
    train2/
    train3/
```

## Notes
- Some `args.yaml` files reference a different absolute path in `save_dir` (e.g. `C:\Users\bilya\Desktop\trafic-sign-yolo\...`). The artifacts in this repo are already copied into the current project folder.
- The default model path in `yolo_webcam.py` expects `runs/detect/train2/weights/best.pt`.
