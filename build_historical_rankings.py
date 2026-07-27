from pathlib import Path
from datetime import datetime
import re

import pandas as pd

from scripts.parser_atg_new import parse_new_atg_format
from scripts.ranking_engine_v3 import (
    add_dynamic_scores,
    calculate_total_score,
)
from badge_engine import (
    assign_badges,
    calculate_spike_score,
)
from loser_badge_helpers import apply_loser_badges_to_race
from badge_rules import (
    get_race_metrics,
    get_loppbadge,
)
from rank68_badge_helpers import apply_rank68_badges


HISTORY_DIR = Path("ranking")
OUTPUT_FILE = Path("historical_rankings.csv")


def read_text(path):
    for encoding in ["utf-8", "cp1252", "latin-1"]:
        try:
            return path.read_text(encoding=encoding)
        except Exception:
            pass

    return path.read_text(errors="replace")


def extract_date(path):
    match = re.search(r"(\d{8})", path.name)
    return match.group(1) if match else ""


def extract_percent_from_raw(horse):
    raw = str(horse.get("raw", ""))
    lines = [
        line.strip()
        for line in raw.splitlines()
        if line.strip()
    ]

    for line in lines:
        if re.fullmatch(r"\d+(?:[.,]\d+)?%", line):
            return float(
                line.replace("%", "").replace(",", ".")
            )

    try:
        return float(horse.get("percent", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def parse_result_file(path):
    text = read_text(path)
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    winners = {}
    index = 0

    while index < len(lines):
        if (
            lines[index].isdigit()
            and 1 <= int(lines[index]) <= 8
        ):
            race_no = int(lines[index])

            for next_index in range(
                index + 1,
                min(index + 8, len(lines)),
            ):
                match = re.match(
                    r"^(\d+)\D+(.+)$",
                    lines[next_index],
                )

                if match:
                    winners[race_no] = {
                        "winner_number": int(match.group(1)),
                        "winner_name": match.group(2).strip(),
                    }
                    break

        index += 1

    return winners


def horse_number(horse):
    number = horse.get("number", 0)

    try:
        number_int = int(number)
    except (TypeError, ValueError):
        number_int = 0

    if number_int == 0:
        horse_name = str(horse.get("horse", ""))
        match = re.match(r"^\s*(\d+)", horse_name)

        if match:
            number_int = int(match.group(1))

    return number_int


def ensure_badges(horse):
    badges = horse.get("badges", [])

    if badges is None:
        horse["badges"] = []
    elif isinstance(badges, str):
        horse["badges"] = [badges] if badges else []
    else:
        horse["badges"] = list(badges)

    return horse


rows = []

start_files = sorted(HISTORY_DIR.glob("start*.txt"))

for start_path in start_files:
    date = extract_date(start_path)

    if not date:
        print(f"Kunde inte läsa datum: {start_path.name}")
        continue

    result_path = HISTORY_DIR / f"resultat{date}.txt"

    if not result_path.exists():
        print(f"Saknar resultat: {date}")
        continue

    try:
        race_date = datetime.strptime(
            date,
            "%Y%m%d",
        ).strftime("%Y-%m-%d")
    except ValueError:
        print(f"Ogiltigt datum: {date}")
        continue

    winners = parse_result_file(result_path)
    raw = read_text(start_path)

    try:
        races = parse_new_atg_format(raw)
    except Exception as error:
        print(
            f"Kunde inte parsa {start_path.name}: {error}"
        )
        continue

    for race_data in races:
        race = race_data["race"]
        horses = race_data["horses"]

        race_no = int(race.get("race_no", 0))

        try:
            horses = add_dynamic_scores(
                horses,
                race,
                race_date=race_date,
            )
        except Exception as error:
            print(
                f"Fel add_dynamic_scores "
                f"{date} avd {race_no}: {error}"
            )
            continue

        for horse in horses:
            ensure_badges(horse)

            horse["total_score"] = calculate_total_score(
                horse
            )

        ranked = sorted(
            horses,
            key=lambda horse: (
                horse.get("total_score", 0),
                -horse_number(horse),
            ),
            reverse=True,
        )

        for model_rank, horse in enumerate(
            ranked,
            start=1,
        ):
            horse["model_rank"] = model_rank

        race_for_badges = dict(race)
        race_for_badges["horses"] = ranked

        try:
            ranked = assign_badges(
                ranked,
                race_for_badges,
            )
        except Exception as error:
            print(
                f"Fel assign_badges "
                f"{date} avd {race_no}: {error}"
            )

        for horse in ranked:
            ensure_badges(horse)

            horse["race_no"] = race_no
            horse["race_track"] = race.get(
                "track",
                "",
            )

            try:
                horse["spike_score"] = (
                    calculate_spike_score(
                        horse,
                        race_for_badges,
                    )
                )
            except Exception as error:
                print(
                    f"Fel spike_score "
                    f"{date} avd {race_no} "
                    f"{horse.get('horse', '')}: {error}"
                )
                horse["spike_score"] = 0

        try:
            ranked = apply_loser_badges_to_race(
                ranked
            )
        except Exception as error:
            print(
                f"Fel loser_badges "
                f"{date} avd {race_no}: {error}"
            )

        for horse in ranked:
            ensure_badges(horse)
            apply_rank68_badges(horse)

        metrics = get_race_metrics(ranked)
        loppbadge = get_loppbadge(metrics)

        spread = metrics.get("spread_1_8", 0)

        for horse in ranked:
            horse["spread"] = spread

        winner_info = winners.get(race_no, {})
        winner_number = winner_info.get(
            "winner_number"
        )

        for horse in ranked:
            number = horse_number(horse)

            badges = horse.get("badges", [])

            rows.append({
                "date": date,
                "race_id": f"{date}_{race_no}",
                "race_no": race_no,
                "track": race.get("track", ""),
                "distance": race.get("distance", ""),
                "start_type": race.get("start", ""),
                "horse": horse.get("horse", ""),
                "number": number,
                "winner_number": winner_number,
                "won": int(
                    winner_number is not None
                    and number == winner_number
                ),
                "model_rank": horse.get(
                    "model_rank",
                    0,
                ),
                "total_score": horse.get(
                    "total_score",
                    0,
                ),
                "spike_score": horse.get(
                    "spike_score",
                    0,
                ),
                "spread": spread,
                "loppbadge": (
                    loppbadge.get("label", "")
                    if isinstance(loppbadge, dict)
                    else str(loppbadge or "")
                ),
                "badges": " | ".join(
                    str(badge)
                    for badge in badges
                    if str(badge).strip()
                ),
                "percent": extract_percent_from_raw(
                    horse
                ),
                "avg_odds": horse.get(
                    "avg_odds",
                    0,
                ),
                "win_score": horse.get(
                    "win_score",
                    0,
                ),
                "form_score": horse.get(
                    "form_score",
                    0,
                ),
                "latest_start_score": horse.get(
                    "latest_start_score",
                    0,
                ),
                "place_score": horse.get(
                    "place_score",
                    0,
                ),
                "speed_score": horse.get(
                    "speed_score",
                    0,
                ),
                "post_score": horse.get(
                    "post_score",
                    0,
                ),
                "driver_score": horse.get(
                    "driver_score",
                    0,
                ),
                "driver_change_score": horse.get(
                    "driver_change_score",
                    0,
                ),
                "record_score": horse.get(
                    "record_score",
                    0,
                ),
                "starts_score": horse.get(
                    "starts_score",
                    0,
                ),
                "spel_score": horse.get(
                    "spel_score",
                    0,
                ),
                "prize_money_score": horse.get(
                    "prize_money_score",
                    0,
                ),
                "recent_prize_score": horse.get(
                    "recent_prize_score",
                    0,
                ),
                "class_change_score": horse.get(
                    "class_change_score",
                    0,
                ),
                "wagon_score": horse.get(
                    "wagon_score",
                    0,
                ),
                "shoe_score": horse.get(
                    "shoe_score",
                    0,
                ),
                "inactivity_score": horse.get(
                    "inactivity_score",
                    0,
                ),
                "stallform_score": horse.get(
                    "stallform_score",
                    0,
                ),
                "custom_score": horse.get(
                    "custom_score",
                    0,
                ),
                "distance_addition_score": horse.get(
                    "distance_addition_score",
                    0,
                ),
                "gender_score": horse.get(
                    "gender_score",
                    0,
                ),
                "gallop_score": horse.get(
                    "gallop_score",
                    0,
                ),
                "post": horse.get("post", 0),
                "prize_money": horse.get(
                    "prize_money",
                    0,
                ),
                "starts": horse.get(
                    "starts",
                    0,
                ),
                "win_percent": horse.get(
                    "win_percent",
                    0,
                ),
                "place_percent": horse.get(
                    "place_percent",
                    0,
                ),
            })


out = pd.DataFrame(rows)

out.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig",
)

print("=" * 80)
print(f"SPARAT {OUTPUT_FILE}")
print("=" * 80)
print("Rader:", len(out))

if out.empty:
    print("Omgångar: 0")
    print("Lopp: 0")
    print("Vinnare matchade: 0")
else:
    print(
        "Omgångar:",
        out["date"].nunique(),
    )
    print(
        "Lopp:",
        out["race_id"].nunique(),
    )
    print(
        "Vinnare matchade:",
        int(out["won"].sum()),
    )
    print(
        "Max total_score:",
        out["total_score"].max(),
    )
    print(
        "Max spike_score:",
        out["spike_score"].max(),
    )
    print(
        "Lopp med badges:",
        out.loc[
            out["badges"].fillna("").ne(""),
            "race_id",
        ].nunique(),
    )