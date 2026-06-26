import pandas as pd
from math import prod

MAX_ROWS = 550

df = pd.read_csv("historical_rankings.csv").fillna(0)


def has_rank68_badge(row):
    return "Rank 6-8" in str(row.get("badges", ""))


def base_pick_count(spread):
    if spread >= 80:
        return 3
    if 60 <= spread <= 69:
        return 4
    if 70 <= spread <= 74:
        return 5
    if 75 <= spread <= 79:
        return 4
    return 5


def race_strength(race):
    r = race.sort_values("model_rank")
    top1 = r.iloc[0]
    top2 = r.iloc[1] if len(r) > 1 else top1

    gap = top1["total_score"] - top2["total_score"]

    return (
        gap
        + top1["spike_score"] / 50
        + top1["spread"] / 20
        + top1["win_score"] / 10
    )


def build_system(round_df):
    selections = {}

    race_strengths = []

    for race_no, race in round_df.groupby("race_no"):
        race = race.sort_values("model_rank").copy()
        spread = float(race["spread"].max())

        n = base_pick_count(spread)

        picks = race[race["model_rank"] <= n]["number"].astype(int).tolist()

        # Lägg till nya Rank 6-8-badgar
        badge_picks = race[
            (race["model_rank"].between(6, 8))
            & (race.apply(has_rank68_badge, axis=1))
        ]["number"].astype(int).tolist()

        picks = sorted(set(picks + badge_picks))

        selections[int(race_no)] = picks

        race_strengths.append((
            int(race_no),
            race_strength(race)
        ))

    def row_count():
        return prod(len(v) for v in selections.values())

    # Om systemet är för stort: spika starkaste lopp först
    for race_no, _ in sorted(race_strengths, key=lambda x: x[1], reverse=True):
        if row_count() <= MAX_ROWS:
            break

        race = round_df[round_df["race_no"] == race_no].sort_values("model_rank")
        selections[race_no] = [int(race.iloc[0]["number"])]

    # Om fortfarande för stort: reducera största lopp stegvis
    while row_count() > MAX_ROWS:
        biggest = max(selections, key=lambda k: len(selections[k]))

        if len(selections[biggest]) <= 1:
            break

        selections[biggest] = selections[biggest][:-1]

    return selections, row_count()


rows = []

for date, round_df in df.groupby("date"):
    if round_df["race_no"].nunique() != 8:
        continue

    selections, rows_count = build_system(round_df)

    hits = 0
    miss_races = []

    for race_no, race in round_df.groupby("race_no"):
        winner = race[race["won"] == 1]

        if winner.empty:
            continue

        winner_number = int(winner.iloc[0]["number"])

        if winner_number in selections.get(int(race_no), []):
            hits += 1
        else:
            miss_races.append(int(race_no))

    rows.append({
        "date": date,
        "rows": rows_count,
        "hits": hits,
        "seven_right": int(hits == 7),
        "eight_right": int(hits == 8),
        "miss_races": ",".join(map(str, miss_races)),
        "system": " / ".join(
            f"A{race_no}:{','.join(map(str, picks))}"
            for race_no, picks in sorted(selections.items())
        )
    })

out = pd.DataFrame(rows)

summary = {
    "rounds": len(out),
    "avg_rows": round(out["rows"].mean(), 1),
    "max_rows": int(out["rows"].max()),
    "eight_right": int(out["eight_right"].sum()),
    "seven_right": int(out["seven_right"].sum()),
    "six_right": int((out["hits"] == 6).sum()),
    "five_right": int((out["hits"] == 5).sum()),
}

print("=" * 80)
print("V86 SYSTEMSIMULERING MAX 550 RADER")
print("=" * 80)

for k, v in summary.items():
    print(f"{k}: {v}")

print()
print(out[["date", "rows", "hits", "miss_races"]].to_string(index=False))

out.to_csv("v86_system_simulation_550.csv", index=False, encoding="utf-8-sig")
pd.DataFrame([summary]).to_csv("v86_system_simulation_550_summary.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("v86_system_simulation_550.csv")
print("v86_system_simulation_550_summary.csv")