import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

HORSES_FILE = BASE / "output" / "horses.json"
CONFIG_FILE = BASE / "config" / "scoring.json"


# ----------------------------
# LOAD DATA
# ----------------------------
def load():
    with open(HORSES_FILE, "r", encoding="utf-8") as f:
        horses = json.load(f)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    return horses, config


# ----------------------------
# DRIVER MULTIPLIER
# ----------------------------
def driver_multiplier(name, config):

    elite = [
        "Örjan Kihlström",
        "Björn Goop",
        "Carl Johan Jepson",
        "Magnus A Djuse"
    ]

    if name in elite:
        return config["driver_bonus_map"]["elite"]

    return config["driver_bonus_map"]["default"]


# ----------------------------
# FORM SCORE (DIN LOGIK)
# ----------------------------
def calculate_form_score(form_lines, config):

    points_map = config["form_points"]

    total = 0
    weight = 1.0

    for result in form_lines[:5]:

        if not result:
            continue

        match = re.search(r"\b([1-5])\b", str(result))

        if match:
            pos = match.group(1)
            total += points_map.get(pos, 0) * weight

        weight *= 0.85

    return total


# ----------------------------
# SCORE ENGINE
# ----------------------------
def score_horse(h, config):

    w = config["weights"]

    form_score = calculate_form_score(h.get("form", []), config)
    driver_score = driver_multiplier(h.get("driver", ""), config)

    odds = h.get("odds", 0)
    speed = h.get("speed", 0)

    # odds inversion (lägre odds = bättre)
    odds_score = 1 / (odds + 1)

    total = (
        form_score * w["form"] +
        driver_score * w["driver"] +
        odds_score * w["odds"] +
        speed * w["speed"]
    )

    return total


# ----------------------------
# MAIN
# ----------------------------
def main():

    horses, config = load()

    ranked = []

    for h in horses:

        h["score"] = score_horse(h, config)
        ranked.append(h)

    ranked.sort(key=lambda x: x["score"], reverse=True)

    print("\n================ RANKING ================\n")

    for i, h in enumerate(ranked[:30], 1):
        print(
            f"{i}. {h['horse']} | Score: {h['score']:.2f} | Kusk: {h.get('driver','')}"
        )

    # DEBUG TOP 5
    print("\n================ DEBUG TOP 5 ================\n")

    for h in ranked[:5]:
        print(h["horse"])
        print(" form:", h.get("form", []))
        print(" odds:", h.get("odds"))
        print(" speed:", h.get("speed"))
        print(" score:", round(h["score"], 2))
        print("----------------")


if __name__ == "__main__":
    main()