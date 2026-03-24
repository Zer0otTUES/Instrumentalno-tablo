from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
import time

import cv2

from config import (
    CAMERA_INDEX_CANDIDATES,
    DEFAULT_MODEL_PATH,
    SIGN_HOLD_SECONDS,
    YOLO_CONFIDENCE,
    YOLO_DETECTION_INTERVAL_S,
    YOLO_IMAGE_SIZE,
)
from core.state import DashboardState

try:
    from ultralytics import YOLO
except Exception as exc:  # pragma: no cover - handled at runtime
    YOLO = None
    YOLO_IMPORT_ERROR = exc
else:
    YOLO_IMPORT_ERROR = None


@dataclass(frozen=True)
class SignDetectionConfig:
    model_path: Path = DEFAULT_MODEL_PATH
    camera_indices: tuple[int, ...] = CAMERA_INDEX_CANDIDATES
    confidence: float = YOLO_CONFIDENCE
    image_size: int = YOLO_IMAGE_SIZE
    detection_interval_s: float = YOLO_DETECTION_INTERVAL_S


def _normalize_sign_label(raw_label: str) -> str:
    normalized = raw_label.strip().lower().replace("_", "-")
    digits = "".join(char for char in normalized if char.isdigit())
    if digits in {"20", "30", "40", "50", "60", "70", "80"}:
        return digits
    if "stop" in normalized:
        return "STOP"
    if "hump" in normalized or "bump" in normalized:
        return "HUMP"
    return raw_label.upper()


def _pick_best_detection(result) -> tuple[str, float] | None:
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return None

    best_index = int(boxes.conf.argmax().item())
    class_id = int(boxes.cls[best_index].item())
    confidence = float(boxes.conf[best_index].item())

    names = result.names
    if isinstance(names, dict):
        raw_label = names.get(class_id, str(class_id))
    else:
        raw_label = names[class_id]

    return _normalize_sign_label(str(raw_label)), confidence


def _open_camera(camera_indices: tuple[int, ...]):
    backends = [cv2.CAP_DSHOW] if hasattr(cv2, "CAP_DSHOW") else []
    backends.append(None)

    for index in camera_indices:
        for backend in backends:
            capture = cv2.VideoCapture(index, backend) if backend is not None else cv2.VideoCapture(index)
            if capture.isOpened():
                capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return capture, index
            capture.release()
    return None, None


class SignDetectorWorker(threading.Thread):
    def __init__(self, state: DashboardState, config: SignDetectionConfig):
        super().__init__(daemon=True)
        self.state = state
        self.config = config
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        if YOLO is None:
            self.state.set_camera_status(f"YOLO import failed: {YOLO_IMPORT_ERROR}", online=False)
            return

        model_path = self.config.model_path
        if not model_path.exists():
            self.state.set_camera_status(f"Model not found: {model_path.name}", online=False)
            return

        self.state.set_camera_status(f"Loading {model_path.name}...", online=False)
        try:
            model = YOLO(str(model_path))
        except Exception as exc:  # pragma: no cover - runtime integration path
            self.state.set_camera_status(f"Model load failed: {exc}", online=False)
            return

        self.state.set_camera_status("Opening camera...", online=False)
        capture, camera_index = _open_camera(self.config.camera_indices)
        if capture is None:
            tried_indices = ", ".join(str(index) for index in self.config.camera_indices)
            self.state.set_camera_status(f"No camera found (tried {tried_indices})", online=False)
            return

        self.state.set_camera_status("YOLO live scan", online=True, camera_index=camera_index)
        next_inference_at = 0.0
        last_detection_at = 0.0

        try:
            while not self._stop_event.is_set():
                ok, frame = capture.read()
                if not ok:
                    self.state.set_camera_status("Camera frame read failed", online=False, camera_index=camera_index)
                    time.sleep(0.2)
                    continue

                now = time.monotonic()
                if now < next_inference_at:
                    time.sleep(0.01)
                    continue

                next_inference_at = now + self.config.detection_interval_s
                try:
                    results = model.predict(
                        frame,
                        conf=self.config.confidence,
                        imgsz=self.config.image_size,
                        verbose=False,
                    )
                except Exception as exc:  # pragma: no cover - runtime integration path
                    self.state.set_camera_status(f"Inference error: {exc}", online=False, camera_index=camera_index)
                    time.sleep(0.5)
                    continue

                best_detection = _pick_best_detection(results[0])
                if best_detection is not None:
                    sign, confidence = best_detection
                    self.state.set_detected_sign(sign, confidence)
                    self.state.set_camera_status("YOLO live scan", online=True, camera_index=camera_index)
                    last_detection_at = now
                elif now - last_detection_at > SIGN_HOLD_SECONDS:
                    self.state.set_detected_sign("SCAN", 0.0)
                    self.state.set_camera_status("Scanning for signs", online=True, camera_index=camera_index)
        finally:
            capture.release()
