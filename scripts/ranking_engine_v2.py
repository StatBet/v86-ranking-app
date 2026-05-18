import json
import re
from pathlib import Path

from scripts.speed_feature import speed_score


# -------------------------------------------------
# PATHS
# -------------------------------------------------

BASE = Path(__file__).resolve().parent.parent

WEIGHTS_FILE = BASE / "config" / "post_position_scores.json"
HORSES_FILE = BASE / "output" / "horses.json"
OUTPUT_FILE = BASE / "output" / "rankings.json"


# -------------------------------------------------
# LOAD CONFIG
# -------------------------------------------------

def load_post_weights():
    with open(WEIGHTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------------------------
# CLEAN / VALIDATION LAYER (NEW)
# -------------------------------------------------

def is_valid_horse(h):
    """
    Filters out noise entries like:
    - random text rows
    - malformed horse entries
    """

    name = h.get("horse", "")

    if not name:
        return False

    # Must contain v/h/s + number (your parser rule)
    if not re.search(r"(v|h|s)\d+", name.lower()):
        return False

    return True


# -------------------------------------------------
# DETERMINE PROFILE KEY
# -------------------------------------------------

def get_profile(distance, start_type):

    dist = int(str(distance)[:4])

    prefix = "auto" if start_type == "auto" else "volt"

    if 1600 <= dist <= 1700:
        return f"{prefix}_short"

    if 2100 <= dist <= 2200:
        return f"{prefix}_medium"

    if 2600 <= dist <= 3200:
        return f"{prefix}_long"

    return None


# -------------------------------------------------
# TRACK SCORE
# -------------------------------------------------

def calculate_track_score(post, distance, start_type, weights):

    profile = get_profile(distance, start_type)

    if not profile:
        return 0

    profile_map = weights.get(profile, {})

    return profile_map.get(str(post), 0)


# -------------------------------------------------
# SPEED SCORE WRAPPER
# -------------------------------------------------

def calculate_speed(horse):

    history = horse.get("history", [])

    return speed_score(
        history=history,
        current_distance="2100",   # V1 default
        start_type="auto"          # V1 default
    )


# -------------------------------------------------
# MAIN ENGINE
# -------------------------------------------------

def rank_horses():

    weights = load_post_weights()

    with open(HORSES_FILE, "r", encoding="utf-8") as f:
        horses = json.load(f)

    results = []

    for h in horses:

        # -------------------------
        # CLEAN FILTER (NEW)
        # -------------------------
        if not is_valid_horse(h):
            continue

        history = h.get("history", [])

        if not history:
            continue

        latest = history[0]

        post = latest.get("post", 0)
        distance = latest.get("distance", 2100)
        start_type = "auto"

        speed = calculate_speed(h)
        track = calculate_track_score(post, distance, start_type, weights)

        total = (
            speed * 0.70 +
            track * 0.30
        )

        results.append({
            "horse": h.get("horse"),
            "speed_score": round(speed, 2),
            "track_score": track,
            "total_score": round(total, 2)
        })

    # sort
    results.sort(key=lambda x: x["total_score"], reverse=True)

    # save
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # print
    print("\n================ RANKING V2 (CLEAN) ================\n")

    for i, r in enumerate(results[:20], 1):
        print(
            f"{i:2}. {r['horse']} | "
            f"SPEED: {r['speed_score']} | "
            f"TRACK: {r['track_score']} | "
            f"TOTAL: {r['total_score']}"
        )


if __name__ == "__main__":
    rank_horses()