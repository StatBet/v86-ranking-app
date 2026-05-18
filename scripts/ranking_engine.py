import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE / "output" / "horses.json"
OUTPUT_FILE = BASE / "output" / "ranking.json"


# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

def load_data():
    return json.loads(INPUT_FILE.read_text(encoding="utf-8"))


# -------------------------------------------------
# TIME PARSER (STABLE)
# -------------------------------------------------

def parse_time(t):

    if not t:
        return None

    t = t.lower().replace(",", ".")

    if t[-1] in ["a", "g"]:
        t = t[:-1]

    try:
        m, s = t.split(".")
        return int(m) * 60 + float(s)
    except:
        return None


# -------------------------------------------------
# SCORING
# -------------------------------------------------

def result_score(result):

    if result == "1":
        return 10
    if result == "2":
        return 7
    if result == "3":
        return 5
    if result and result.isdigit():
        return max(0, 4 - int(result))
    return 0


def speed_score(distance, time_sec):

    if not time_sec or not distance:
        return 0

    return distance / time_sec


def race_score(race):

    try:
        distance = int(race.get("distance") or 0)
    except:
        distance = 0

    time_sec = parse_time(race.get("time"))
    res = race.get("result")

    speed = speed_score(distance, time_sec)
    place = result_score(res)

    return speed * 100 + place


# -------------------------------------------------
# HORSE SCORE
# -------------------------------------------------

def horse_score(horse):

    history = horse.get("history", [])

    if not history:
        return 0

    scores = []

    for i, race in enumerate(history[:5]):

        score = race_score(race)

        weight = 1.0 / (i + 1)

        scores.append(score * weight)

    return sum(scores) / sum(1.0 / (i + 1) for i in range(len(scores)))


# -------------------------------------------------
# STRICT VALIDATION (FIX)
# -------------------------------------------------

def is_valid_horse(h):

    # must be dict
    if not isinstance(h, dict):
        return False

    # must have required keys
    if "horse" not in h or "history" not in h:
        return False

    # horse name must be valid string
    if not isinstance(h["horse"], str) or len(h["horse"]) < 2:
        return False

    # history must be list
    if not isinstance(h["history"], list):
        return False

    # must contain at least 1 valid race entry
    has_valid_race = False

    for r in h["history"]:
        if isinstance(r, dict):
            # require at least date or result to consider valid race
            if r.get("date") or r.get("result"):
                has_valid_race = True
                break

    return has_valid_race


# -------------------------------------------------
# RANKING ENGINE
# -------------------------------------------------

def build_ranking(data):

    ranking = []

    for horse in data:

        # 🚨 CLEAN INPUT ONLY
        if not is_valid_horse(horse):
            continue

        score = horse_score(horse)

        ranking.append({
            "horse": horse.get("horse"),
            "driver": horse.get("driver"),
            "score": round(score, 4)
        })

    ranking.sort(key=lambda x: x["score"], reverse=True)

    return ranking


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():

    data = load_data()

    ranking = build_ranking(data)

    OUTPUT_FILE.write_text(
        json.dumps(ranking, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n================ RANKING TOP 10 ================\n")

    for r in ranking[:10]:
        print(f"{r['horse']} | {r['driver']} | {r['score']}")


if __name__ == "__main__":
    main()