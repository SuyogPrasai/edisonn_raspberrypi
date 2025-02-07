from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Car:
    MIN_SPEED: int
    MAX_SPEED: int

    ACCELERATION_DELAY: float
    DECELERATION_DELAY: float

    ACCELERATION_INCREMENT: int
    DECELERATION_INCREMENT: int

    LEFT_ANGLE: int
    RIGHT_ANGLE: int
    FRONT_ANGLE: int

    car_states: Dict[str, int] = field(default_factory=lambda: {
        "current_speed": 0,
        "current_direction": 0
    })
