import pandas as pd

DATASET = "ml_dataset.csv"

df = pd.read_csv(DATASET)

df = df[df["won"].isin([0, 1])]

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

    rows.append({
        "won": int(top["won"]),
        "driver": top["raw"] if "raw" in top else "",
        "driver_name": top["driver"] if "driver" in race.columns else "",
        "win_percent": top["win_percent"],
        "place_percent": top["place_percent"],
        "form_score": top["form_score"],
        "avg_odds": top["avg_odds"],
        "avg_time": top["avg_time"],
        "post": top["post"],
        "field_size": top["field_size"],
        "score_gap": top["total_score"] - second["total_score"]
    })

analysis = pd.DataFrame(rows)

print("=" * 80)
print("TOTALT")
print("=" * 80)
print("Spikar:", len(analysis))
print("Rätt:", int(analysis["won"].sum()))
print("Träff%:", round(analysis["won"].mean() * 100, 1))


def bucket_report(df, column, bins, labels):

    print()
    print("=" * 80)
    print(column.upper())
    print("=" * 80)

    temp = df.copy()

    temp["bucket"] = pd.cut(
        temp[column],
        bins=bins,
        labels=labels,
        include_lowest=True
    )

    report = (
        temp.groupby("bucket", observed=False)
        .agg(
            spikar=("won", "count"),
            ratt=("won", "sum")
        )
        .reset_index()
    )

    report["traff_pct"] = round(
        report["ratt"] / report["spikar"] * 100,
        1
    )

    print(report.to_string(index=False))


bucket_report(
    analysis,
    "win_percent",
    [-1, 20, 40, 60, 80, 100],
    ["0-20", "20-40", "40-60", "60-80", "80-100"]
)

bucket_report(
    analysis,
    "place_percent",
    [-1, 40, 60, 80, 100],
    ["0-40", "40-60", "60-80", "80-100"]
)

bucket_report(
    analysis,
    "score_gap",
    [-999, 5, 10, 15, 20, 25, 30, 999],
    ["0-5", "5-10", "10-15", "15-20", "20-25", "25-30", "30+"]
)

bucket_report(
    analysis,
    "post",
    [0, 3, 6, 8, 12, 20],
    ["1-3", "4-6", "7-8", "9-12", "13+"]
)

bucket_report(
    analysis,
    "field_size",
    [0, 8, 10, 12, 20],
    ["<=8", "9-10", "11-12", "13+"]
)

print()
print("=" * 80)
print("KUSKAR SOM TOPPRANKAD HÄST")
print("=" * 80)

if "driver_name" in analysis.columns:

    drivers = (
        analysis.groupby("driver_name")
        .agg(
            spikar=("won", "count"),
            ratt=("won", "sum")
        )
        .reset_index()
    )

    drivers = drivers[
        drivers["spikar"] >= 5
    ]

    drivers["traff_pct"] = round(
        drivers["ratt"] / drivers["spikar"] * 100,
        1
    )

    drivers = drivers.sort_values(
        ["traff_pct", "spikar"],
        ascending=[False, False]
    )

    print(drivers.to_string(index=False))