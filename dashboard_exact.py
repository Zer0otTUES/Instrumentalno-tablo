from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime
from pathlib import Path

import pygame


PROJECT_ROOT = Path(__file__).resolve().parent
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from config import (  # noqa: E402
    CAMERA_INDEX_CANDIDATES,
    DEFAULT_MODEL_PATH,
    FPS,
    IDLE_RPM,
    MAX_RPM,
    MAX_SPEED_KMH,
    SHOW_N_BELOW_SPEED,
    WINDOW_TITLE,
    YOLO_CONFIDENCE,
)
from core.blindspot_logic import toggle_blindspot  # noqa: E402
from core.blink_logic import advance_blink, toggle_turn_signal  # noqa: E402
from core.drivetrain import advance_distance, sync_from_rpm, sync_from_speed  # noqa: E402
from core.sign_detection import SignDetectionConfig, SignDetectorWorker  # noqa: E402
from core.state import DashboardSnapshot, DashboardState  # noqa: E402


BG_PATH = PROJECT_ROOT / "assets" / "dashboard_bg.png"

WHITE = (245, 245, 250)
PURPLE = (190, 75, 255)
PURPLE_DIM = (46, 24, 68)
PURPLE_FILL = (98, 42, 158)
ORANGE = (255, 145, 20)
ORANGE_FILL = (132, 68, 16)
RED = (225, 36, 34)
RED_DARK = (80, 8, 12)
GREEN = (45, 255, 126)
GREEN_DIM = (18, 58, 36)
YELLOW = (255, 214, 72)
BLACK = (0, 0, 0)

SPEED_CENTER = (835, 500)
UNIT_CENTER = (835, 612)
GEAR_CENTER = (1235, 508)
SIGN_CENTER = (424, 502)
WARNING_CENTER = (835, 735)
CLOCK_CENTER = (835, 812)

LEFT_ARROW_CENTER = (222, 216)
RIGHT_ARROW_CENTER = (1450, 216)

RPM_SEGMENTS = 13
RPM_SEGMENT_POLYGONS = [
    [(481, 205), (518, 205), (548, 239), (515, 239)],
    [(542, 205), (579, 205), (604, 239), (571, 239)],
    [(601, 205), (638, 205), (657, 239), (625, 239)],
    [(661, 205), (695, 205), (709, 239), (679, 239)],
    [(717, 205), (751, 205), (757, 239), (730, 239)],
    [(773, 205), (807, 205), (807, 239), (778, 239)],
    [(827, 205), (862, 205), (855, 239), (827, 239)],
    [(882, 205), (917, 205), (904, 239), (874, 239)],
    [(938, 205), (973, 205), (955, 239), (923, 239)],
    [(994, 205), (1031, 205), (1006, 239), (973, 239)],
    [(1054, 205), (1088, 205), (1060, 239), (1028, 239)],
    [(1115, 205), (1148, 205), (1115, 239), (1083, 239)],
    [(1174, 205), (1207, 205), (1169, 239), (1138, 239)],
]

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
    parser = argparse.ArgumentParser(description="Motorcycle dashboard using the exact background skin")
    parser.add_argument("--camera", type=int, default=None, help="Preferred camera index. Default: auto try 0,1,2")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH, help="Path to YOLO weights")
    parser.add_argument("--conf", type=float, default=YOLO_CONFIDENCE, help="Detection confidence threshold")
    parser.add_argument("--no-camera", action="store_true", help="Run without YOLO/camera")
    parser.add_argument("--scale", type=float, default=1.0, help="Window scale for the 1672x941 background")
    return parser


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


def handle_keydown(state: DashboardState, key: int) -> str | None:
    with state.lock:
        if key == pygame.K_UP:
            state.rpm = min(MAX_RPM, state.rpm + 250)
            return "rpm"
        if key == pygame.K_DOWN:
            state.rpm = max(IDLE_RPM, state.rpm - 250)
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


class ExactDashboardUI:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.bg = pygame.image.load(BG_PATH).convert()
        self.width, self.height = self.bg.get_size()

        self.speed_font = pygame.font.SysFont("bahnschrift", 150, bold=True)
        self.unit_font = pygame.font.SysFont("bahnschrift", 42, bold=True)
        self.gear_font = pygame.font.SysFont("bahnschrift", 95, bold=True)
        self.clock_font = pygame.font.SysFont("bahnschrift", 30, bold=True)
        self.sign_font = pygame.font.SysFont("bahnschrift", 48, bold=True)
        self.sign_small_font = pygame.font.SysFont("bahnschrift", 28, bold=True)
        self.warning_font = pygame.font.SysFont("bahnschrift", 26, bold=True)

    def draw(self, snapshot: DashboardSnapshot, blink_phase: bool) -> None:
        self.surface.blit(self.bg, (0, 0))

        self.draw_arrow(LEFT_ARROW_CENTER, "left", snapshot.blink_left, blink_phase)
        self.draw_arrow(RIGHT_ARROW_CENTER, "right", snapshot.blink_right, blink_phase)
        self.draw_blindspot("left", snapshot.blind_left)
        self.draw_blindspot("right", snapshot.blind_right)

        self.draw_rpm_bar(snapshot.rpm)
        self.draw_sign(snapshot.detected_sign, snapshot.detected_sign_confidence)
        self.draw_speed(snapshot.speed_kmh)
        self.draw_gear(snapshot)
        self.draw_warning(snapshot.warning and blink_phase)
        self.draw_clock()

    def draw_glow_text(
        self,
        value: object,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        center: tuple[int, int],
        glow_color: tuple[int, int, int] | None = None,
        glow_size: int = 2,
    ) -> None:
        glow_color = glow_color or color
        text = str(value)
        glow_offsets = [
            (-glow_size, 0),
            (glow_size, 0),
            (0, -glow_size),
            (0, glow_size),
            (-glow_size, -glow_size),
            (glow_size, glow_size),
        ]

        for dx, dy in glow_offsets:
            surf = font.render(text, True, glow_color)
            surf.set_alpha(70)
            rect = surf.get_rect(center=(center[0] + dx, center[1] + dy))
            self.surface.blit(surf, rect)

        surf = font.render(text, True, color)
        rect = surf.get_rect(center=center)
        self.surface.blit(surf, rect)

    def draw_speed(self, speed_kmh: float) -> None:
        self.draw_glow_text(int(speed_kmh), self.speed_font, WHITE, SPEED_CENTER, (120, 90, 180), 3)
        self.draw_glow_text("km/h", self.unit_font, PURPLE, UNIT_CENTER, PURPLE, 2)

    def draw_gear(self, snapshot: DashboardSnapshot) -> None:
        is_neutral = snapshot.speed_kmh < SHOW_N_BELOW_SPEED and snapshot.rpm <= IDLE_RPM + 150
        gear_text = "N" if is_neutral else str(snapshot.gear)
        self.draw_glow_text(gear_text, self.gear_font, ORANGE, GEAR_CENTER, ORANGE, 3)

    def draw_clock(self) -> None:
        current_time = datetime.now().strftime("%H:%M")
        self.draw_glow_text(current_time, self.clock_font, WHITE, CLOCK_CENTER, (100, 100, 120), 2)

    def draw_warning(self, active: bool) -> None:
        if not active:
            return

        cx, cy = WARNING_CENTER
        glow = pygame.Surface((118, 108), pygame.SRCALPHA)
        pygame.draw.polygon(glow, (*RED, 82), [(59, 8), (14, 90), (104, 90)])
        self.surface.blit(glow, (cx - 59, cy - 54))

        pygame.draw.polygon(self.surface, RED, [(cx, cy - 32), (cx - 30, cy + 27), (cx + 30, cy + 27)])
        pygame.draw.polygon(self.surface, (255, 162, 162), [(cx, cy - 32), (cx - 30, cy + 27), (cx + 30, cy + 27)], width=3)
        self.draw_glow_text("!", self.warning_font, WHITE, (cx, cy + 4), RED_DARK, 1)

    def draw_sign(self, sign_value: str, _confidence: float) -> None:
        label = (sign_value or "SCAN").upper()
        cx, cy = SIGN_CENTER
        sign = self.create_sign_surface(label)
        self.surface.blit(sign, sign.get_rect(center=(cx, cy)))

    def create_sign_surface(self, label: str) -> pygame.Surface:
        size = 148
        scale = 4
        large_size = size * scale
        surface = pygame.Surface((large_size, large_size), pygame.SRCALPHA)
        center = large_size // 2

        if label.isdigit():
            pygame.draw.circle(surface, (255, 18, 18, 44), (center, center), 70 * scale)
            pygame.draw.circle(surface, (235, 28, 35), (center, center), 62 * scale)
            pygame.draw.circle(surface, (255, 255, 255), (center, center), 46 * scale)
            pygame.draw.circle(surface, (190, 12, 16), (center, center), 62 * scale, 3 * scale)
            font = pygame.font.SysFont("bahnschrift", 50 * scale, bold=True)
            text = font.render(label, True, BLACK)
            surface.blit(text, text.get_rect(center=(center, center + 3 * scale)))
        elif label == "STOP":
            points = []
            radius = 61 * scale
            for index in range(8):
                angle = math.radians(22.5 + index * 45)
                points.append((center + int(math.cos(angle) * radius), center + int(math.sin(angle) * radius)))
            pygame.draw.polygon(surface, (220, 24, 32), points)
            pygame.draw.polygon(surface, WHITE, points, width=4 * scale)
            font = pygame.font.SysFont("bahnschrift", 31 * scale, bold=True)
            text = font.render("STOP", True, WHITE)
            surface.blit(text, text.get_rect(center=(center, center + 2 * scale)))
        elif label == "HUMP":
            points = [
                (center, center - 65 * scale),
                (center + 65 * scale, center),
                (center, center + 65 * scale),
                (center - 65 * scale, center),
            ]
            pygame.draw.polygon(surface, YELLOW, points)
            pygame.draw.polygon(surface, BLACK, points, width=4 * scale)
            pygame.draw.arc(
                surface,
                BLACK,
                pygame.Rect(center - 34 * scale, center - 4 * scale, 68 * scale, 38 * scale),
                math.radians(0),
                math.radians(180),
                7 * scale,
            )
            pygame.draw.line(surface, BLACK, (center - 44 * scale, center + 34 * scale), (center + 44 * scale, center + 34 * scale), 5 * scale)
        else:
            rect = pygame.Rect(14 * scale, 42 * scale, 120 * scale, 64 * scale)
            pygame.draw.rect(surface, (15, 11, 24), rect, border_radius=9 * scale)
            pygame.draw.rect(surface, PURPLE, rect, width=2 * scale, border_radius=9 * scale)
            font = pygame.font.SysFont("bahnschrift", 28 * scale, bold=True)
            text = font.render("SCAN", True, PURPLE)
            surface.blit(text, text.get_rect(center=(center, center)))

        return pygame.transform.smoothscale(surface, (size, size))

    def draw_arrow(self, center: tuple[int, int], direction: str, enabled: bool, blink_phase: bool) -> None:
        if not enabled:
            return

        is_lit = blink_phase
        color = GREEN if is_lit else GREEN_DIM
        alpha = 76 if is_lit else 22
        cx, cy = center

        if direction == "left":
            points = [
                (cx - 58, cy),
                (cx - 8, cy - 34),
                (cx - 8, cy - 16),
                (cx + 66, cy - 16),
                (cx + 66, cy + 16),
                (cx - 8, cy + 16),
                (cx - 8, cy + 34),
            ]
        else:
            points = [
                (cx + 58, cy),
                (cx + 8, cy - 34),
                (cx + 8, cy - 16),
                (cx - 66, cy - 16),
                (cx - 66, cy + 16),
                (cx + 8, cy + 16),
                (cx + 8, cy + 34),
            ]

        glow = pygame.Surface((180, 110), pygame.SRCALPHA)
        shifted = [(x - cx + 90, y - cy + 55) for x, y in points]
        pygame.draw.polygon(glow, (*color, alpha), shifted)
        self.surface.blit(glow, (cx - 90, cy - 55))
        pygame.draw.polygon(self.surface, color, points)

    def draw_blindspot(self, side: str, active: bool) -> None:
        if not active:
            return

        layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        tick = pygame.time.get_ticks() / 1000.0
        panel_center = (92, 505) if side == "left" else (1580, 505)
        start_angle = math.radians(-42) if side == "left" else math.radians(138)
        end_angle = math.radians(42) if side == "left" else math.radians(222)

        for index in range(4):
            phase = (tick * 1.25 + index * 0.19) % 1.0
            pulse = 0.45 + 0.55 * math.sin((phase * math.tau) - math.pi / 2)
            alpha = int(34 + pulse * 92)
            radius_x = 52 + index * 30
            radius_y = 82 + index * 38
            rect = pygame.Rect(0, 0, radius_x * 2, radius_y * 2)
            rect.center = panel_center

            width = max(2, 6 - index)
            pygame.draw.arc(layer, (*ORANGE, alpha), rect, start_angle, end_angle, width)
            pygame.draw.arc(layer, (255, 214, 112, max(20, alpha // 3)), rect, start_angle, end_angle, 1)

        chevron_alpha = int(95 + 55 * math.sin(tick * 5.0))
        cx = 170 if side == "left" else 1502
        cy = 505
        if side == "left":
            chevrons = [
                [(cx - 20, cy - 42), (cx - 52, cy), (cx - 20, cy + 42)],
                [(cx + 22, cy - 34), (cx - 5, cy), (cx + 22, cy + 34)],
            ]
        else:
            chevrons = [
                [(cx + 20, cy - 42), (cx + 52, cy), (cx + 20, cy + 42)],
                [(cx - 22, cy - 34), (cx + 5, cy), (cx - 22, cy + 34)],
            ]

        for points in chevrons:
            pygame.draw.lines(layer, (*ORANGE, chevron_alpha), False, points, width=5)
            pygame.draw.lines(layer, (255, 218, 130, max(20, chevron_alpha // 3)), False, points, width=1)

        self.surface.blit(layer, (0, 0))

    def draw_rpm_bar(self, rpm: float) -> None:
        rpm_level = round(max(0.0, min(rpm, MAX_RPM)) / MAX_RPM * RPM_SEGMENTS)

        for i, points in enumerate(RPM_SEGMENT_POLYGONS):
            if i >= rpm_level:
                continue

            fill = ORANGE_FILL if i >= 10 else PURPLE_FILL
            glow_color = ORANGE if i >= 10 else PURPLE
            x_values = [point[0] for point in points]
            y_values = [point[1] for point in points]
            left = min(x_values) - 16
            top = min(y_values) - 16
            width = max(x_values) - min(x_values) + 32
            height = max(y_values) - min(y_values) + 32
            local_points = [(x - left, y - top) for x, y in points]

            glow = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.polygon(glow, (*glow_color, 58), local_points)
            self.surface.blit(glow, (left, top))
            pygame.draw.polygon(self.surface, fill, points)


def draw_scaled(source: pygame.Surface, destination: pygame.Surface) -> None:
    if source.get_size() == destination.get_size():
        destination.blit(source, (0, 0))
        return

    scaled = pygame.transform.smoothscale(source, destination.get_size())
    destination.blit(scaled, (0, 0))


def main() -> None:
    args = build_parser().parse_args()
    print_controls()

    if not BG_PATH.exists():
        raise FileNotFoundError(f"Background image not found: {BG_PATH}")

    pygame.init()
    bg_probe = pygame.image.load(BG_PATH)
    design_size = bg_probe.get_size()
    bg_probe = None

    scale = max(0.1, args.scale)
    window_size = (round(design_size[0] * scale), round(design_size[1] * scale))
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption(f"{WINDOW_TITLE} - Exact UI")
    clock = pygame.time.Clock()

    design_surface = pygame.Surface(design_size).convert()
    ui = ExactDashboardUI(design_surface)
    state = DashboardState()

    worker = None
    if args.no_camera:
        state.set_camera_status("Camera disabled", online=False)
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
            draw_scaled(design_surface, screen)
            pygame.display.flip()
    finally:
        if worker is not None:
            worker.stop()
            worker.join(timeout=2.0)
        pygame.quit()


if __name__ == "__main__":
    main()
