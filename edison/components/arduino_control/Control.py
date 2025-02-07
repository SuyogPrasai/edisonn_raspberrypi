import os
import time

from dotenv import load_dotenv
from typing import List, Tuple

from edison.models.Car import Car

class CarControlelr:

    def __init__(self):
        self.car = Car(
            car_states={
                "current_speed": 0,
                "current_direction": os.getenv("FRONT_ANGLE", 90)
            },
            
            current_speed=0,
            current_direction=int(os.getenv("FRONT_ANGLE", 90)),

            MIN_SPEED=os.getenv("MIN_SPEED", 100),
            MAX_SPEED=os.getenv("MAX_SPEED", 255),

            ACCELERATION_DELAY=float(os.getenv("ACCELERATION_DELAY", 0.1)),
            DECELERATION_DELAY=float(os.getenv("DECELERATION_DELAY", 0.1)),

            ACCELERATION_INCREMENT=int(os.getenv("ACCELERATION_INCREMENT", 5)),
            DECELERATION_INCREMENT=int(os.getenv("DECELERATION_INCREMENT", 5)),

            LEFT_ANGLE=os.getenv("LEFT_ANGLE", 120),
            RIGHT_ANGLE=os.getenv("RIGHT_ANGLE", 60),
            FRONT_ANGLE=os.getenv("FRONT_ANGLE", 90)
        )


    def update_car_state(self) -> int:
        current_state = self.car.control_states
        
