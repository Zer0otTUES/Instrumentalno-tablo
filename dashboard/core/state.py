from __future__ import annotations

from dataclasses import dataclass, field
import threading


@dataclass(frozen=True)
class DashboardSnapshot:
    speed_kmh: float
    rpm: float
    gear: int
    blink_left: bool
    blink_right: bool
    warning: bool
    blind_left: bool
    blind_right: bool
    detected_sign: str
    detected_sign_confidence: float
    camera_status: str
    camera_online: bool
    camera_index: int | None
    trip_km: float
    odo_km: float


@dataclass
class DashboardState:
    speed_kmh: float = 0.0
    rpm: float = 1400.0
    gear: int = 1

    blink_left: bool = False
    blink_right: bool = False
    warning: bool = False

    blind_left: bool = False
    blind_right: bool = False

    detected_sign: str = "SCAN"
    detected_sign_confidence: float = 0.0
    camera_status: str = "Initializing camera..."
    camera_online: bool = False
    camera_index: int | None = None

    trip_km: float = 12.4
    odo_km: float = 18342.0

    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def snapshot(self) -> DashboardSnapshot:
        with self.lock:
            return DashboardSnapshot(
                speed_kmh=self.speed_kmh,
                rpm=self.rpm,
                gear=self.gear,
                blink_left=self.blink_left,
                blink_right=self.blink_right,
                warning=self.warning,
                blind_left=self.blind_left,
                blind_right=self.blind_right,
                detected_sign=self.detected_sign,
                detected_sign_confidence=self.detected_sign_confidence,
                camera_status=self.camera_status,
                camera_online=self.camera_online,
                camera_index=self.camera_index,
                trip_km=self.trip_km,
                odo_km=self.odo_km,
            )

    def set_detected_sign(self, sign: str, confidence: float = 0.0) -> None:
        with self.lock:
            self.detected_sign = sign
            self.detected_sign_confidence = confidence

    def set_camera_status(
        self,
        status: str,
        *,
        online: bool | None = None,
        camera_index: int | None = None,
    ) -> None:
        with self.lock:
            self.camera_status = status
            if online is not None:
                self.camera_online = online
            if camera_index is not None:
                self.camera_index = camera_index
