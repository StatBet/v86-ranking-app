from dataclasses import dataclass


@dataclass
class Horse:

    name: str
    driver: str
    post_position: int = 0

    speed_score: float = 0
    form_score: float = 0
    driver_score: float = 0
    value_score: float = 0

    total_score: float = 0