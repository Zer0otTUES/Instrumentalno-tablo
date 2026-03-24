import math
import pygame
from config import RING_COLOR, TICK_COLOR, TEXT_COLOR, MUTED_COLOR


class Gauge:
    def __init__(self, center, radius, min_value, max_value, label, unit, pointer_color):
        self.cx, self.cy = center
        self.radius = radius
        self.min_value = min_value
        self.max_value = max_value
        self.label = label
        self.unit = unit
        self.pointer_color = pointer_color
        self.start_angle = 140
        self.end_angle = 400

    def _value_to_angle(self, value):
        value = max(self.min_value, min(self.max_value, value))
        ratio = (value - self.min_value) / (self.max_value - self.min_value)
        deg = self.start_angle + ratio * (self.end_angle - self.start_angle)
        return math.radians(deg)

    def draw(self, surface, value, font_big, font_small, font_label, display_text=None):
        pygame.draw.circle(surface, (10, 18, 30), (self.cx, self.cy), self.radius)
        pygame.draw.circle(surface, RING_COLOR, (self.cx, self.cy), self.radius, 6)
        pygame.draw.circle(surface, (7, 16, 27), (self.cx, self.cy), self.radius - 36, 2)

        for i in range(0, 23):
            tick_value = self.min_value + i * (self.max_value - self.min_value) / 22
            angle = self._value_to_angle(tick_value)

            x1 = self.cx + math.cos(angle) * (self.radius - 24)
            y1 = self.cy + math.sin(angle) * (self.radius - 24)
            x2 = self.cx + math.cos(angle) * (self.radius - 46)
            y2 = self.cy + math.sin(angle) * (self.radius - 46)

            pygame.draw.line(surface, TICK_COLOR, (x1, y1), (x2, y2), 3)

        angle = self._value_to_angle(value)
        px = self.cx + math.cos(angle) * (self.radius - 72)
        py = self.cy + math.sin(angle) * (self.radius - 72)

        pygame.draw.line(surface, self.pointer_color, (self.cx, self.cy), (px, py), 6)
        pygame.draw.circle(surface, self.pointer_color, (self.cx, self.cy), 11)
        pygame.draw.circle(surface, (230, 240, 255), (self.cx, self.cy), 11, 2)

        label_s = font_label.render(self.label, True, MUTED_COLOR)
        unit_s = font_small.render(self.unit, True, MUTED_COLOR)

        if display_text is None:
            shown_value = str(int(value))
        else:
            shown_value = str(display_text)

        value_s = font_big.render(shown_value, True, TEXT_COLOR)

        surface.blit(label_s, label_s.get_rect(center=(self.cx, self.cy - 18)))
        surface.blit(value_s, value_s.get_rect(center=(self.cx, self.cy + 20)))
        surface.blit(unit_s, unit_s.get_rect(center=(self.cx, self.cy + 62)))