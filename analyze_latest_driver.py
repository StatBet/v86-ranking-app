import pandas as pd

df = pd.read_csv("ml_dataset.csv")
df = df[df["won"].isin([0, 1])]

rows = []

for race_id, race in df.groupby("race_id"):
    race = race.sort_values("total_score", ascending=False).reset_index(drop=True)

    if len(race) < 2:
        continue

    if race["won"].sum() != 1:
        continue

    top = race.iloc[0]
    second = race.iloc[1]

    score_gap = top["total_score"] - second["total_score"]

    rows.append({
        "won": int(top["won"]),
        "latest_start_score": top["latest_start_score"],
        "driver_score": top["driver_score"],
        "post": top["post"],
        "field_size": top["field_size"],
        "score_gap": score_gap,
        "form_score": top["form_score"],
        "win_percent": top["win_percent"],
        "place_percent": top["place_percent"],
    })

a = pd.DataFrame(rows)


def test(name, condition):
    subset = a[condition]
    total = len(subset)
    wins = int(subset["won"].sum()) if total else 0
    pct = round(wins / total * 100, 1) if total else 0

    print(f"{name:<55} {total:>4} spikar  {wins:>3} rätt  {pct:>5}%")


print("=" * 90)
print("LATEST START SCORE")
print("=" * 90)

test("latest_start_score > 0", a["latest_start_score"] > 0)
test("latest_start_score >= 5", a["latest_start_score"] >= 5)
test("latest_start_score >= 10", a["latest_start_score"] >= 10)
test("latest_start_score = 0", a["latest_start_score"] == 0)


print()
print("=" * 90)
print("DRIVER SCORE")
print("=" * 90)

test("driver_score > 0", a["driver_score"] > 0)
test("driver_score >= 5", a["driver_score"] >= 5)
test("driver_score >= 10", a["driver_score"] >= 10)
test("driver_score = 0", a["driver_score"] == 0)


print()
print("=" * 90)
print("LATEST + DRIVER")
print("=" * 90)

test(
    "latest > 0 + driver > 0",
    (a["latest_start_score"] > 0) &
    (a["driver_score"] > 0)
)

test(
    "latest >= 5 + driver >= 5",
    (a["latest_start_score"] >= 5) &
    (a["driver_score"] >= 5)
)

test(
    "latest >= 10 + driver >= 5",
    (a["latest_start_score"] >= 10) &
    (a["driver_score"] >= 5)
)


print()
print("=" * 90)
print("POST + FIELD + GAP")
print("=" * 90)

test(
    "post <= 6",
    a["post"] <= 6
)

test(
    "post <= 6 + field <= 10",
    (a["post"] <= 6) &
    (a["field_size"] <= 10)
)

test(
    "post <= 6 + field <= 12",
    (a["post"] <= 6) &
    (a["field_size"] <= 12)
)

test(
    "post <= 6 + score_gap >= 10",
    (a["post"] <= 6) &
    (a["score_gap"] >= 10)
)

test(
    "post <= 6 + score_gap >= 20",
    (a["post"] <= 6) &
    (a["score_gap"] >= 20)
)

test(
    "field <= 10 + score_gap >= 10",
    (a["field_size"] <= 10) &
    (a["score_gap"] >= 10)
)

test(
    "field <= 10 + score_gap >= 20",
    (a["field_size"] <= 10) &
    (a["score_gap"] >= 20)
)

test(
    "post <= 6 + field <= 10 + gap >= 10",
    (a["post"] <= 6) &
    (a["field_size"] <= 10) &
    (a["score_gap"] >= 10)
)

test(
    "post <= 6 + field <= 10 + gap >= 20",
    (a["post"] <= 6) &
    (a["field_size"] <= 10) &
    (a["score_gap"] >= 20)
)


print()
print("=" * 90)
print("SUPERKOMBOS")
print("=" * 90)

test(
    "latest > 0 + driver > 0 + post <= 6",
    (a["latest_start_score"] > 0) &
    (a["driver_score"] > 0) &
    (a["post"] <= 6)
)

test(
    "latest > 0 + driver > 0 + post <= 6 + field <= 10",
    (a["latest_start_score"] > 0) &
    (a["driver_score"] > 0) &
    (a["post"] <= 6) &
    (a["field_size"] <= 10)
)

test(
    "latest > 0 + driver > 0 + post <= 6 + field <= 12",
    (a["latest_start_score"] > 0) &
    (a["driver_score"] > 0) &
    (a["post"] <= 6) &
    (a["field_size"] <= 12)
)

test(
    "latest > 0 + driver > 0 + post <= 6 + gap >= 10",
    (a["latest_start_score"] > 0) &
    (a["driver_score"] > 0) &
    (a["post"] <= 6) &
    (a["score_gap"] >= 10)
)

test(
    "latest > 0 + driver > 0 + post <= 6 + field <= 10 + gap >= 10",
    (a["latest_start_score"] > 0) &
    (a["driver_score"] > 0) &
    (a["post"] <= 6) &
    (a["field_size"] <= 10) &
    (a["score_gap"] >= 10)
)


print()
print("=" * 90)
print("DÅLIGA ZONER")
print("=" * 90)

test(
    "post >= 7 + field >= 11",
    (a["post"] >= 7) &
    (a["field_size"] >= 11)
)

test(
    "post >= 7 + field >= 11 + gap < 20",
    (a["post"] >= 7) &
    (a["field_size"] >= 11) &
    (a["score_gap"] < 20)
)

test(
    "post >= 9 + field >= 12",
    (a["post"] >= 9) &
    (a["field_size"] >= 12)
)

test(
    "post >= 9 + field >= 13",
    (a["post"] >= 9) &
    (a["field_size"] >= 13)
)