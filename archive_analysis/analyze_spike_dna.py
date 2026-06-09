import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

valid_races = (
    df.groupby("race_id")["won"]
    .sum()
    .reset_index()
)

valid_races = valid_races[
    valid_races["won"] == 1
]["race_id"]

df = df[
    df["race_id"].isin(valid_races)
].copy()

signal = df[
    (df["model_rank"].between(6, 8))
    & (df["place_percent"] >= 50)
    & (df["win_percent"] >= 25)
    & (df["form_score"] >= 20)
    & (df["latest_start_score"] >= 5)
].copy()

print("=" * 80)
print("SPIKE DNA")
print("=" * 80)

print()
print("Antal kandidater:")
print(len(signal))

print()
print("Vinnare:")
print(int(signal["won"].sum()))

if len(signal):

    print()
    print("Träff%:")
    print(
        round(
            signal["won"].sum()
            / len(signal)
            * 100,
            1
        )
    )

print()
print("=" * 80)
print("MODEL RANK")
print("=" * 80)

print(
    signal["model_rank"]
    .value_counts()
    .sort_index()
    .to_string()
)

print()
print("=" * 80)
print("VINNARE")
print("=" * 80)

print(
    signal[
        signal["won"] == 1
    ][
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "win_percent",
            "place_percent",
            "form_score",
            "latest_start_score",
            "avg_odds"
        ]
    ].to_string(index=False)
)