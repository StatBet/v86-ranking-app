from rankings.signal_builder import build_signals
from rankings.engine import calculate_score
from rankings.config import RANKING_CONFIG


def rank_race(horses):
    results = []

    for h in horses:
        signals = build_signals(h["data"])
        score = calculate_score(signals, RANKING_CONFIG)

        results.append({
            "name": h["name"],
            "score": score,
            "signals": signals
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results