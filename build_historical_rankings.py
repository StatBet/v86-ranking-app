from pathlib import Path
import re
import pandas as pd

from scripts.parser_v2 import parse_input
from scripts.ranking_engine_v3 import (
    add_dynamic_scores,
    calculate_total_score,
)
from badge_rules import get_race_metrics, get_loppbadge
from rank68_badge_helpers import apply_rank68_badges
from badge_engine import calculate_spike_score


HISTORY_DIR = Path("ranking")


def read_text(path):
    for enc in ["utf-8", "cp1252", "latin-1"]:
        try:
            return path.read_text(encoding=enc)
        except Exception:
            pass
    return path.read_text(errors="replace")


def extract_date(path):
    m = re.search(r"(\d{8})", path.name)
    return m.group(1) if m else ""

def extract_percent_from_raw(horse):
    raw = str(horse.get("raw", ""))
    lines = [x.strip() for x in raw.splitlines() if x.strip()]

    for line in lines:
        if re.fullmatch(r"\d+%", line):
            return int(line.replace("%", ""))

    return horse.get("percent", 0)


def parse_result_file(path):
    text = read_text(path)
    lines = [x.strip() for x in text.splitlines() if x.strip()]

    winners = {}
    i = 0

    while i < len(lines):
        if lines[i].isdigit() and 1 <= int(lines[i]) <= 8:
            avd = int(lines[i])

            for j in range(i + 1, min(i + 8, len(lines))):
                m = re.match(r"^(\d+)\D+(.+)$", lines[j])
                if m:
                    winners[avd] = {
                        "winner_number": int(m.group(1)),
                        "winner_name": m.group(2).strip(),
                    }
                    break
        i += 1

    return winners


rows = []

start_files = sorted(HISTORY_DIR.glob("start*.txt"))

for start_path in start_files:
    date = extract_date(start_path)
    result_path = HISTORY_DIR / f"resultat{date}.txt"

    if not result_path.exists():
        print(f"Saknar resultat: {date}")
        continue

    winners = parse_result_file(result_path)
    raw = read_text(start_path)

    try:
        races = parse_input(raw)
    except Exception as e:
        print(f"Kunde inte parsa {start_path.name}: {e}")
        continue

    for race_data in races:
        race = race_data["race"]
        horses = race_data["horses"]

        try:
            horses = add_dynamic_scores(horses, race)
        except Exception as e:
            print(f"Fel add_dynamic_scores {date} avd {race.get('race_no')}: {e}")
            continue

        ranked = []

        for h in horses:
            h["total_score"] = calculate_total_score(h)
            ranked.append(h)

        ranked = sorted(
            ranked,
            key=lambda x: x.get("total_score", 0),
            reverse=True
        )

        for model_rank, h in enumerate(ranked, start=1):
            h["model_rank"] = model_rank

        metrics = get_race_metrics(ranked)
        loppbadge = get_loppbadge(metrics)
        spread = metrics.get("spread_1_8", 0)

        avd = int(race.get("race_no", 0))
        winner_info = winners.get(avd, {})
        winner_number = winner_info.get("winner_number")

        race_for_spike = dict(race)
        race_for_spike["horses"] = ranked

        for h in ranked:
            h["spread"] = spread
            h["spike_score"] = calculate_spike_score(h, race_for_spike)
            h["badges"] = []
            h = apply_rank68_badges(h)

            number = h.get("number", 0)

            try:
                number_int = int(number)
            except Exception:
                number_int = 0

            if number_int == 0:
                horse_name = str(h.get("horse", ""))
                m = re.match(r"^\s*(\d+)", horse_name)
                if m:
                    number_int = int(m.group(1))

            
            rows.append({
                "date": date,
                "race_id": f"{date}_{avd}",
                "race_no": avd,
                "track": race.get("track", ""),
                "distance": race.get("distance", ""),
                "start_type": race.get("start", ""),
                "horse": h.get("horse", ""),
                "number": number_int,
                "winner_number": winner_number,
                "won": int(number_int == winner_number),
                "model_rank": h.get("model_rank", 0),
                "total_score": h.get("total_score", 0),
                "spike_score": h.get("spike_score", 0),
                "spread": spread,
                "loppbadge": loppbadge.get("label", ""),
                "badges": " | ".join(h.get("badges", [])),
                "percent": extract_percent_from_raw(h),
                "avg_odds": h.get("avg_odds", 0),
                "win_score": h.get("win_score", 0),
                "form_score": h.get("form_score", 0),
                "latest_start_score": h.get("latest_start_score", 0),
                "place_score": h.get("place_score", 0),
                "speed_score": h.get("speed_score", 0),
                "post": h.get("post", 0),
            })

out = pd.DataFrame(rows)

out.to_csv("historical_rankings.csv", index=False, encoding="utf-8-sig")

print("=" * 80)
print("SPARAT historical_rankings.csv")
print("=" * 80)
print("Rader:", len(out))
print("Omgångar:", out["date"].nunique())
print("Lopp:", out["race_id"].nunique())
print("Vinnare matchade:", int(out["won"].sum()))