def toggle_blindspot(left_active: bool, right_active: bool, side: str) -> tuple[bool, bool]:
    if side == "left":
        return not left_active, right_active
    if side == "right":
        return left_active, not right_active
    raise ValueError(f"Unsupported blind spot side: {side}")
