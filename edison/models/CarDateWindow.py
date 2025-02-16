from dataclasses import dataclass

@dataclass
class CarData:
    speed: int
    direction: str
    location: tuple[float, float]
    cpu_usage: int
    ram_usage: int