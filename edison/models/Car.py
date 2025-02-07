from dataclasses import dataclass
from typing import Dict

@dataclass
class Car:
    car_states: Dict[str, bool] = {
        "current_speed": int,
        "current_direction": int
    }

    MIN_SPEED: int
    MAX_SPEED: int

    ACCELERATION_DELAY: float
    DECELERATION_DELAY: float

    ACCELERATION_INCREMENT: int
    DECELERATION_INCREMENT: int

    LEFT_ANGLE: int
    RIGHT_ANGLE: int
    FRONT_ANGLE: int
