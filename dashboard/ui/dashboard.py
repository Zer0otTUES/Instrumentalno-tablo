import pygame

from config import (
    BG_COLOR,
    MUTED_COLOR,
    PANEL_COLOR,
    RPM_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHOW_N_BELOW_SPEED,
    SPEED_COLOR,
    TEXT_COLOR,
)
from ui.gauge import Gauge
from ui.indicators import draw_blind_dot, draw_sign_badge, draw_turn_button, draw_warning


class DashboardUI:
    def __init__(self, screen):
        self.screen = screen

        self.font_speed = pygame.font.SysFont("Segoe UI", 54, bold=True)
        self.font_mid = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_label = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.font_sign = pygame.font.SysFont("Segoe UI", 38, bold=True)

        self.speed_gauge = Gauge((260, 310), 210, 0, 220, "SPEED", "KM/H", SPEED_COLOR)
        self.rpm_gauge = Gauge((764, 310), 210, 0, 12000, "RPM", "RPM", RPM_COLOR)

        self.left_arrow_rect = pygame.Rect(28, 514, 62, 62)
        self.right_arrow_rect = pygame.Rect(934, 514, 62, 62)
        self.blind_left_center = (56, 560)
        self.blind_right_center = (968, 560)

        self.panel_rect = pygame.Rect(20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40)
        self.sign_rect = pygame.Rect(436, 102, 152, 152)
        self.gear_rect = pygame.Rect(452, 360, 120, 92)

    def draw(self, snapshot, blink_phase):
        self.screen.fill(BG_COLOR)

        pygame.draw.rect(self.screen, PANEL_COLOR, self.panel_rect, border_radius=26)
        pygame.draw.rect(self.screen, (22, 34, 52), self.panel_rect, 1, border_radius=26)

        speed_display = "N" if snapshot.speed_kmh < SHOW_N_BELOW_SPEED else str(int(snapshot.speed_kmh))
        self.speed_gauge.draw(
            self.screen,
            snapshot.speed_kmh,
            self.font_speed,
            self.font_small,
            self.font_label,
            display_text=speed_display,
        )
        self.rpm_gauge.draw(
            self.screen,
            snapshot.rpm,
            self.font_speed,
            self.font_small,
            self.font_label,
            display_text=str(int(snapshot.rpm)),
        )

        sign_label = self.font_label.render("TRAFFIC SIGN", True, MUTED_COLOR)
        self.screen.blit(sign_label, sign_label.get_rect(center=(self.sign_rect.centerx, 76)))
        draw_sign_badge(
            self.screen,
            self.sign_rect,
            snapshot.detected_sign,
            snapshot.detected_sign_confidence,
            self.font_sign,
            self.font_mid,
            self.font_small,
        )

        camera_index = "-" if snapshot.camera_index is None else str(snapshot.camera_index)
        status_color = TEXT_COLOR if snapshot.camera_online else (255, 124, 124)
        camera_text = self.font_small.render(f"CAM {camera_index}", True, status_color)
        status_text = self.font_label.render(snapshot.camera_status, True, MUTED_COLOR)
        self.screen.blit(camera_text, camera_text.get_rect(center=(self.sign_rect.centerx, 270)))
        self.screen.blit(status_text, status_text.get_rect(center=(self.sign_rect.centerx, 292)))

        draw_warning(self.screen, (510, 320), snapshot.warning, blink_phase, self.font_mid)

        pygame.draw.rect(self.screen, (18, 27, 40), self.gear_rect, border_radius=18)
        pygame.draw.rect(self.screen, (30, 45, 64), self.gear_rect, 1, border_radius=18)
        gear_label = self.font_label.render("GEAR", True, MUTED_COLOR)
        gear_value = self.font_mid.render(str(snapshot.gear), True, TEXT_COLOR)
        self.screen.blit(gear_label, gear_label.get_rect(center=(self.gear_rect.centerx, self.gear_rect.top + 22)))
        self.screen.blit(gear_value, gear_value.get_rect(center=(self.gear_rect.centerx, self.gear_rect.bottom - 28)))

        draw_turn_button(self.screen, self.left_arrow_rect, "left", snapshot.blink_left, blink_phase, self.font_label)
        draw_turn_button(self.screen, self.right_arrow_rect, "right", snapshot.blink_right, blink_phase, self.font_label)
        draw_blind_dot(self.screen, self.blind_left_center, snapshot.blind_left)
        draw_blind_dot(self.screen, self.blind_right_center, snapshot.blind_right)

        trip_label = self.font_small.render(f"Trip {snapshot.trip_km:.1f} km", True, TEXT_COLOR)
        odo_label = self.font_small.render(f"Odo {int(snapshot.odo_km)} km", True, TEXT_COLOR)
        hints_label = self.font_label.render("Arrows speed/rpm | A D blink | W warn | Q E blind | 1-9 manual sign", True, MUTED_COLOR)
        self.screen.blit(trip_label, (412, 500))
        self.screen.blit(odo_label, (412, 528))
        self.screen.blit(hints_label, hints_label.get_rect(center=(SCREEN_WIDTH // 2, 568)))
