from __future__ import annotations

import argparse
from pathlib import Path

import pygame

from config import (
    CAMERA_INDEX_CANDIDATES,
    DEFAULT_MODEL_PATH,
    FPS,
    MAX_RPM,
    MAX_SPEED_KMH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WINDOW_TITLE,
    YOLO_CONFIDENCE,
)
from core.blindspot_logic import toggle_blindspot
from core.blink_logic import advance_blink, toggle_turn_signal
from core.drivetrain import advance_distance, sync_from_rpm, sync_from_speed
from core.sign_detection import SignDetectionConfig, SignDetectorWorker
from core.state import DashboardState
from ui.dashboard import DashboardUI


MANUAL_SIGN_KEYS = {
    pygame.K_1: "20",
    pygame.K_2: "30",
    pygame.K_3: "40",
    pygame.K_4: "50",
    pygame.K_5: "60",
    pygame.K_6: "70",
    pygame.K_7: "80",
    pygame.K_8: "HUMP",
    pygame.K_9: "STOP",
    pygame.K_0: "SCAN",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Motorcycle dashboard with YOLO traffic sign detection")
    parser.add_argument("--camera", type=int, default=None, help="Preferred camera index. Default: auto try 0,1,2")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH, help="Path to YOLO weights")
    parser.add_argument("--conf", type=float, default=YOLO_CONFIDENCE, help="Detection confidence threshold")
    parser.add_argument("--no-camera", action="store_true", help="Run the dashboard without YOLO/camera")
    return parser


def handle_keydown(state: DashboardState, key: int) -> str | None:
    with state.lock:
        if key == pygame.K_UP:
            state.rpm = min(MAX_RPM, state.rpm + 250)
            return "rpm"
        if key == pygame.K_DOWN:
            state.rpm = max(1400, state.rpm - 250)
            return "rpm"
        if key == pygame.K_RIGHT:
            state.speed_kmh = min(MAX_SPEED_KMH, state.speed_kmh + 3)
            return "speed"
        if key == pygame.K_LEFT:
            state.speed_kmh = max(0.0, state.speed_kmh - 3)
            return "speed"
        if key == pygame.K_a:
            state.blink_left, state.blink_right = toggle_turn_signal(state.blink_left, state.blink_right, "left")
            return None
        if key == pygame.K_d:
            state.blink_left, state.blink_right = toggle_turn_signal(state.blink_left, state.blink_right, "right")
            return None
        if key == pygame.K_w:
            state.warning = not state.warning
            return None
        if key == pygame.K_q:
            state.blind_left, state.blind_right = toggle_blindspot(state.blind_left, state.blind_right, "left")
            return None
        if key == pygame.K_e:
            state.blind_left, state.blind_right = toggle_blindspot(state.blind_left, state.blind_right, "right")
            return None
        if key in MANUAL_SIGN_KEYS:
            state.detected_sign = MANUAL_SIGN_KEYS[key]
            state.detected_sign_confidence = 1.0 if key != pygame.K_0 else 0.0
            return None
    return None


def print_controls() -> None:
    print("Controls:")
    print("  Up/Down    -> change RPM")
    print("  Left/Right -> change speed")
    print("  A / D      -> left/right blinkers")
    print("  W          -> warning triangle")
    print("  Q / E      -> blind spot indicators")
    print("  1..7       -> manual speed sign")
    print("  8 / 9 / 0  -> HUMP / STOP / SCAN")
    print("  Esc        -> exit")


def main() -> None:
    args = build_parser().parse_args()
    print_controls()

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    state = DashboardState()
    ui = DashboardUI(screen)

    worker = None
    if args.no_camera:
        state.set_camera_status("Camera disabled by flag", online=False)
    else:
        camera_indices = (args.camera,) if args.camera is not None else CAMERA_INDEX_CANDIDATES
        detection_config = SignDetectionConfig(
            model_path=Path(args.model).expanduser(),
            camera_indices=camera_indices,
            confidence=args.conf,
        )
        worker = SignDetectorWorker(state, detection_config)
        worker.start()

    blink_timer = 0
    blink_phase = True
    sync_mode = "rpm"
    running = True

    try:
        while running:
            dt_ms = clock.tick(FPS)
            blink_timer, blink_phase = advance_blink(blink_timer, blink_phase, dt_ms)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        continue
                    requested_sync_mode = handle_keydown(state, event.key)
                    if requested_sync_mode is not None:
                        sync_mode = requested_sync_mode

            with state.lock:
                if sync_mode == "rpm":
                    state.speed_kmh, state.rpm, state.gear = sync_from_rpm(state.rpm, state.gear)
                else:
                    state.speed_kmh, state.rpm, state.gear = sync_from_speed(state.speed_kmh, state.gear)
                state.trip_km, state.odo_km = advance_distance(
                    state.trip_km,
                    state.odo_km,
                    state.speed_kmh,
                    dt_ms / 1000.0,
                )

            ui.draw(state.snapshot(), blink_phase)
            pygame.display.flip()
    finally:
        if worker is not None:
            worker.stop()
            worker.join(timeout=2.0)
        pygame.quit()


if __name__ == "__main__":
    main()
