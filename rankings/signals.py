from dataclasses import dataclass


@dataclass
class HorseSignals:
    form_trend: float = 0.0
    speed_rating: float = 0.0
    distance_fit: float = 0.0
    driver_synergy: float = 0.0
    consistency: float = 0.0