import math

import pygame

from config import GREEN, MUTED_COLOR, RED, TEXT_COLOR, YELLOW


def draw_turn_button(surface, rect, direction, active, blink_phase, font):
    is_lit = active and blink_phase
    fill = (20, 30, 44) if not is_lit else (18, 52, 40)
    edge = (34, 48, 70) if not is_lit else GREEN
    icon_color = (88, 108, 136) if not is_lit else GREEN

    pygame.draw.rect(surface, fill, rect, border_radius=16)
    pygame.draw.rect(surface, edge, rect, width=2, border_radius=16)

    if direction == "left":
        points = [
            (rect.left + 14, rect.centery),
            (rect.left + 30, rect.top + 14),
            (rect.left + 30, rect.top + 24),
            (rect.right - 12, rect.top + 24),
            (rect.right - 12, rect.bottom - 24),
            (rect.left + 30, rect.bottom - 24),
            (rect.left + 30, rect.bottom - 14),
        ]
    else:
        points = [
            (rect.right - 14, rect.centery),
            (rect.right - 30, rect.top + 14),
            (rect.right - 30, rect.top + 24),
            (rect.left + 12, rect.top + 24),
            (rect.left + 12, rect.bottom - 24),
            (rect.right - 30, rect.bottom - 24),
            (rect.right - 30, rect.bottom - 14),
        ]

    pygame.draw.polygon(surface, icon_color, points)
    label = font.render(direction[0].upper(), True, TEXT_COLOR)
    surface.blit(label, label.get_rect(center=rect.center))


def draw_blind_dot(surface, center, active):
    color = RED if active else (58, 74, 96)
    glow_color = (120, 28, 28) if active else (24, 34, 46)

    pygame.draw.circle(surface, glow_color, center, 15)
    pygame.draw.circle(surface, color, center, 9)
    pygame.draw.circle(surface, TEXT_COLOR, center, 9, 1)


def draw_warning(surface, center, active, blink_phase, font):
    color = YELLOW if active and blink_phase else (84, 98, 118)
    points = [
        (center[0], center[1] - 32),
        (center[0] - 28, center[1] + 24),
        (center[0] + 28, center[1] + 24),
    ]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (20, 24, 30), points, 2)

    bang = font.render("!", True, (20, 24, 30))
    surface.blit(bang, bang.get_rect(center=(center[0], center[1] + 4)))


def draw_sign_badge(surface, rect, sign, confidence, font_big, font_mid, font_small):
    pygame.draw.rect(surface, (18, 27, 40), rect, border_radius=18)
    pygame.draw.rect(surface, (30, 45, 64), rect, 1, border_radius=18)

    center = (rect.centerx, rect.centery + 6)
    sign_text = sign.upper()

    if sign_text.isdigit():
        pygame.draw.circle(surface, RED, center, 46)
        pygame.draw.circle(surface, (246, 246, 246), center, 36)
        text_surface = font_big.render(sign_text, True, (18, 18, 18))
        surface.blit(text_surface, text_surface.get_rect(center=center))
    elif sign_text == "STOP":
        points = []
        for index in range(8):
            angle = math.radians(22.5 + index * 45)
            points.append(
                (
                    center[0] + math.cos(angle) * 42,
                    center[1] + math.sin(angle) * 42,
                )
            )
        pygame.draw.polygon(surface, RED, points)
        pygame.draw.polygon(surface, (248, 248, 248), points, 3)
        text_surface = font_mid.render("STOP", True, (248, 248, 248))
        surface.blit(text_surface, text_surface.get_rect(center=center))
    elif sign_text == "HUMP":
        points = [
            (center[0], center[1] - 40),
            (center[0] + 40, center[1]),
            (center[0], center[1] + 40),
            (center[0] - 40, center[1]),
        ]
        pygame.draw.polygon(surface, YELLOW, points)
        pygame.draw.polygon(surface, (28, 28, 28), points, 3)
        text_surface = font_small.render("HUMP", True, (28, 28, 28))
        surface.blit(text_surface, text_surface.get_rect(center=center))
    else:
        pygame.draw.circle(surface, (30, 42, 58), center, 44)
        pygame.draw.circle(surface, (56, 72, 94), center, 44, 2)
        text_surface = font_small.render("SCAN", True, MUTED_COLOR)
        surface.blit(text_surface, text_surface.get_rect(center=center))

    confidence_text = "waiting" if confidence <= 0 else f"{confidence * 100:.0f}%"
    confidence_surface = font_small.render(confidence_text, True, MUTED_COLOR)
    surface.blit(confidence_surface, confidence_surface.get_rect(center=(rect.centerx, rect.bottom - 16)))
