import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict

BASE = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE / "input" / "input_word.txt"
OUTPUT_FILE = BASE / "output" / "horses.json"


# -------------------------------------------------
# MODELS
# -------------------------------------------------

@dataclass
class RaceHistory:
    date: str
    track: str
    driver: str
    result: str
    distance: int
    post: str | None
    time: str | None
    odds: str | None
    prize: str | None
    wagon: str | None


@dataclass
class Horse:
    horse: str
    driver: str
    history: list


# -------------------------------------------------
# CLEAN INPUT
# -------------------------------------------------

def clean(line: str):
    return line.replace("\u00a0", " ").strip()


# -------------------------------------------------
# DETECTION
# -------------------------------------------------

def is_horse_line(line: str):
    return bool(re.search(r"(v|h|s)\s*\d+", line.lower()))


def extract_driver(line: str):
    line = re.split(r"\d+%", line)[0]
    return re.sub(r"\s+", " ", line).strip()


# -------------------------------------------------
# VALIDATORS
# -------------------------------------------------

def is_post(t: str):
    return re.fullmatch(r"\d{1,2}", t) is not None


def is_valid_odds(t: str):
    return re.fullmatch(r"\d{1,3},\d{1,2}", t) is not None


def is_prize(t: str):
    return "'" in t


def is_wagon_type(t: str):
    return t.lower() in {"vanlig", "amerikansk"}


def is_junk(t: str):
    t = t.lower()
    return t in {"-", "logga", "in", "för", "kommentarer"} or "logga" in t


# -------------------------------------------------
# STRICT TIME RULE (LOCKED)
# -------------------------------------------------

def is_valid_time(t: str):
    t = t.lower()
    return re.fullmatch(r"\d{1,2},\d{1}(a|g)?", t) is not None


# -------------------------------------------------
# WAGON NOISE FILTER
# -------------------------------------------------

def is_wagon_noise_token(t: str):
    t = t.lower()
    return (
        re.fullmatch(r"\d{1,2}ag", t) is not None
        or t == "uag"
    )


# -------------------------------------------------
# ROW PARSER
# -------------------------------------------------

def parse_row_best(row):

    post = None
    time_value = None
    odds = None
    prize = None
    wagon = None

    used = set()

    # POST
    for i, t in enumerate(row):
        if is_post(t):
            post = t
            used.add(i)
            break

    # TIME
    for i, t in enumerate(row):
        if i in used:
            continue
        if is_valid_time(t):
            time_value = t
            used.add(i)
            break

    # ODDS
    for i, t in enumerate(row):
        if i in used:
            continue
        if is_valid_odds(t):
            odds = t
            used.add(i)
            break

    # PRIZE
    for i, t in enumerate(row):
        if i in used:
            continue
        if is_prize(t):
            prize = t
            used.add(i)
            break

    # WAGON
    wagon_tokens = []

    for i, t in enumerate(row):
        if i in used:
            continue

        if is_wagon_type(t):
            wagon = t
            continue

        if is_wagon_noise_token(t):
            continue

        if is_junk(t):
            continue

        wagon_tokens.append(t)

    if wagon_tokens:
        wagon = (wagon + " " if wagon else "") + " ".join(wagon_tokens).strip()

    return post, time_value, odds, prize, wagon


# -------------------------------------------------
# HISTORY PARSER
# -------------------------------------------------

def parse_history_row(date_line, race_line):

    parts = race_line.split()

    if len(parts) < 5:
        return None

    track = parts[0].split("-")[0]

    result_index = None
    for i, token in enumerate(parts):
        if re.fullmatch(r"(?:[0-7](?:uag|ag|a|g)?|d)", token.lower()):
            result_index = i
            break

    if result_index is None:
        return None

    driver = " ".join(parts[1:result_index])
    result = parts[result_index]

    distance = 0
    if result_index + 1 < len(parts):
        try:
            distance = int(parts[result_index + 1])
        except:
            pass

    post = None
    time_value = None
    odds = None
    prize = None
    wagon = None

    if ":" in parts:
        c = parts.index(":")
        row = parts[c + 1:]
        post, time_value, odds, prize, wagon = parse_row_best(row)

    return RaceHistory(
        date=date_line,
        track=track,
        driver=driver,
        result=result,
        distance=distance,
        post=post,
        time=time_value,
        odds=odds,
        prize=prize,
        wagon=wagon
    )


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():

    raw = INPUT_FILE.read_text(encoding="utf-8").splitlines()
    lines = [clean(l) for l in raw if clean(l)]

    horses = []

    print("LINES:", len(lines))

    i = 0

    while i < len(lines):

        line = lines[i]

        if is_horse_line(line):

            horse_name = line
            driver = ""
            history = []

            if i + 1 < len(lines):
                nxt = lines[i + 1]
                if not is_horse_line(nxt):
                    driver = extract_driver(nxt)

            for j in range(i + 1, min(i + 60, len(lines) - 1)):

                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", lines[j]):

                    parsed = parse_history_row(lines[j], lines[j + 1])

                    if parsed:
                        history.append(asdict(parsed))

            horses.append(asdict(Horse(
                horse=horse_name,
                driver=driver,
                history=history
            )))

        i += 1

    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(horses, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # -------------------------------------------------
    # DEBUG
    # -------------------------------------------------

    print("\n================ PARSED HORSES ================\n")
    print(len(horses))

    assert len(horses) == 143, f"Parser broken: expected 143 horses, got {len(horses)}"

    for h in horses[:2]:
        print(f"\nHORSE: {h['horse']}")
        print(f"DRIVER: {h['driver']}")
        print("HISTORY:")

        for r in h["history"][:3]:
            print(
                f"{r['date']} | {r['track']} | {r['driver']} | {r['result']} | {r['distance']} | {r['post']} | {r['time']} | {r['odds']} | {r['prize']} | {r['wagon']}"
            )


if __name__ == "__main__":
    main()