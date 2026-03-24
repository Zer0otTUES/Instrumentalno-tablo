from config import (
    FINAL_REDUCTION,
    GEAR_RATIOS,
    IDLE_RPM,
    MAX_RPM,
    MAX_SPEED_KMH,
    MIN_RPM_PER_GEAR,
    PRIMARY_REDUCTION,
    SHOW_N_BELOW_SPEED,
    UPSHIFT_RPM,
    WHEEL_CIRCUMFERENCE_M,
)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _total_ratio(gear: int) -> float:
    return PRIMARY_REDUCTION * FINAL_REDUCTION * GEAR_RATIOS[gear]


def speed_from_rpm(rpm: float, gear: int) -> float:
    wheel_rpm = rpm / _total_ratio(gear)
    speed_kmh = wheel_rpm * WHEEL_CIRCUMFERENCE_M * 60 / 1000
    return _clamp(speed_kmh, 0.0, MAX_SPEED_KMH)


def rpm_from_speed(speed_kmh: float, gear: int) -> float:
    if speed_kmh <= 0:
        return IDLE_RPM

    wheel_rpm = (speed_kmh * 1000 / 60) / WHEEL_CIRCUMFERENCE_M
    return wheel_rpm * _total_ratio(gear)


def sync_from_rpm(rpm: float, gear: int) -> tuple[float, float, int]:
    gear = max(min(gear, max(GEAR_RATIOS)), min(GEAR_RATIOS))
    rpm = _clamp(rpm, IDLE_RPM, MAX_RPM)

    while gear < max(GEAR_RATIOS) and rpm > UPSHIFT_RPM:
        next_gear = gear + 1
        rpm = rpm * _total_ratio(next_gear) / _total_ratio(gear)
        gear = next_gear

    while gear > min(GEAR_RATIOS) and rpm < MIN_RPM_PER_GEAR[gear]:
        previous_gear = gear - 1
        rpm = rpm * _total_ratio(previous_gear) / _total_ratio(gear)
        gear = previous_gear

    speed_kmh = speed_from_rpm(rpm, gear)
    if speed_kmh < SHOW_N_BELOW_SPEED and rpm <= IDLE_RPM + 150:
        speed_kmh = 0.0

    return speed_kmh, max(IDLE_RPM, rpm), gear


def sync_from_speed(speed_kmh: float, gear: int) -> tuple[float, float, int]:
    gear = max(min(gear, max(GEAR_RATIOS)), min(GEAR_RATIOS))
    speed_kmh = _clamp(speed_kmh, 0.0, MAX_SPEED_KMH)

    rpm = rpm_from_speed(speed_kmh, gear)
    while gear < max(GEAR_RATIOS) and rpm > UPSHIFT_RPM:
        gear += 1
        rpm = rpm_from_speed(speed_kmh, gear)

    while gear > min(GEAR_RATIOS) and rpm < MIN_RPM_PER_GEAR[gear]:
        gear -= 1
        rpm = rpm_from_speed(speed_kmh, gear)

    if speed_kmh < SHOW_N_BELOW_SPEED:
        rpm = IDLE_RPM

    return speed_kmh, max(IDLE_RPM, min(rpm, MAX_RPM)), gear


def advance_distance(trip_km: float, odo_km: float, speed_kmh: float, dt_seconds: float) -> tuple[float, float]:
    delta_km = speed_kmh * dt_seconds / 3600
    return trip_km + delta_km, odo_km + delta_km
