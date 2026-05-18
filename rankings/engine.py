from dataclasses import dataclass
from rankings.config import RANKING_CONFIG


@dataclass
class HorseSignals:
    form_trend: float = 0.0
    speed_rating: float = 0.0
    distance_fit: float = 0.0
    driver_synergy: float = 0.0
    consistency: float = 0.0


def calculate_score(s: HorseSignals, config=RANKING_CONFIG):
    score = 0.0

    # Form / utveckling
    if "form" in config:
        score += s.form_trend * config["form"]

    # Kusk + häst
    if "driver" in config:
        score += s.driver_synergy * config["driver"]

    # Distans
    if "distance" in config:
        score += s.distance_fit * config["distance"]

    # Stabilitet / jämnhet
    if "track" in config:
        score += s.consistency * config["track"]

    # Tempo / tid / speed
    if "time" in config:
        score += s.speed_rating * config["time"]

    return score