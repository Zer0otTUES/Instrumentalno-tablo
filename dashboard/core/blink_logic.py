from config import BLINK_INTERVAL_MS


def advance_blink(timer_ms: int, blink_phase: bool, dt_ms: int) -> tuple[int, bool]:
    timer_ms += dt_ms
    while timer_ms >= BLINK_INTERVAL_MS:
        timer_ms -= BLINK_INTERVAL_MS
        blink_phase = not blink_phase
    return timer_ms, blink_phase


def toggle_turn_signal(left_active: bool, right_active: bool, side: str) -> tuple[bool, bool]:
    if side == "left":
        return not left_active, False
    if side == "right":
        return False, not right_active
    raise ValueError(f"Unsupported turn signal side: {side}")
