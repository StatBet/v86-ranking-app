import pandas as pd

df = pd.read_csv("ml_dataset.csv")

rows = []

for race_id, race in df.groupby("race_id"):

    race = race.sort_values(
        "total_score",
        ascending=False
    ).reset_index(drop=True)

    if len(race) < 2:
        continue

    top = race.iloc[0]
    second = race.iloc[1]

    score_gap = (
        top["total_score"]
        - second["total_score"]
    )

    post = top["post"]
    field_size = top["field_size"]

    if post <= 6:
        post_group = "1-6"
    elif post <= 8:
        post_group = "7-8"
    else:
        post_group = "9+"

    if field_size <= 10:
        field_group = "<=10"
    elif field_size <= 12:
        field_group = "11-12"
    else:
        field_group = "13+"

    if score_gap < 10:
        gap_group = "<10"
    elif score_gap < 20:
        gap_group = "10-20"
    else:
        gap_group = "20+"

    rows.append({
        "won": int(top["won"]),
        "post_group": post_group,
        "field_group": field_group,
        "gap_group": gap_group
    })

env = pd.DataFrame(rows)

print("=" * 80)
print("POST + FÄLTSTORLEK")
print("=" * 80)

table = (
    env.groupby(
        ["post_group", "field_group"]
    )
    .agg(
        spikar=("won", "count"),
        ratt=("won", "sum")
    )
    .reset_index()
)

table["traff_pct"] = round(
    table["ratt"] / table["spikar"] * 100,
    1
)

print(
    table.sort_values(
        "traff_pct",
        ascending=False
    ).to_string(index=False)
)

print()
print("=" * 80)
print("POST + GAP")
print("=" * 80)

table = (
    env.groupby(
        ["post_group", "gap_group"]
    )
    .agg(
        spikar=("won", "count"),
        ratt=("won", "sum")
    )
    .reset_index()
)

table["traff_pct"] = round(
    table["ratt"] / table["spikar"] * 100,
    1
)

print(
    table.sort_values(
        "traff_pct",
        ascending=False
    ).to_string(index=False)
)

print()
print("=" * 80)
print("FÄLTSTORLEK + GAP")
print("=" * 80)

table = (
    env.groupby(
        ["field_group", "gap_group"]
    )
    .agg(
        spikar=("won", "count"),
        ratt=("won", "sum")
    )
    .reset_index()
)

table["traff_pct"] = round(
    table["ratt"] / table["spikar"] * 100,
    1
)

print(
    table.sort_values(
        "traff_pct",
        ascending=False
    ).to_string(index=False)
)