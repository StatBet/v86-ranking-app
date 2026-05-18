from rankings.engine import HorseFactors, calculate_score

def build_horse_factors(horse):
    """
    Här mappar vi ATG-data → rankingfaktorer
    """

    return HorseFactors(
        form=50,       # placeholder
        driver=50,     # placeholder
        distance=50,   # placeholder
        track=50,      # placeholder
        time=50        # placeholder
    )


def rank_race(race):
    results = []

    for start in race.get("starts", []):
        horse = start.get("horse", {})

        factors = build_horse_factors(horse)
        score = calculate_score(factors)

        results.append({
            "name": horse.get("name"),
            "score": score
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)