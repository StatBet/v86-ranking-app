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

rank68 = df[
    df["model_rank"].between(6, 8)
].copy()

tests = {
    "Place >= 50":
        rank68["place_percent"] >= 50,

    "Win >= 25":
        rank68["win_percent"] >= 25,

    "Form >= 20":
        rank68["form_score"] >= 20,

    "Latest >= 5":
        rank68["latest_start_score"] >= 5,

    "Place >=50 + Win >=25":
        (
            (rank68["place_percent"] >= 50)
            &
            (rank68["win_percent"] >= 25)
        ),

    "Place >=50 + Latest >=5":
        (
            (rank68["place_percent"] >= 50)
            &
            (rank68["latest_start_score"] >= 5)
        ),

    "Alla fyra":
        (
            (rank68["place_percent"] >= 50)
            &
            (rank68["win_percent"] >= 25)
            &
            (rank68["form_score"] >= 20)
            &
            (rank68["latest_start_score"] >= 5)
        )
}

print("=" * 80)
print("RANK 6-8 SIGNALER")
print("=" * 80)

for name, mask in tests.items():

    subset = rank68[mask]

    total = len(subset)
    wins = int(subset["won"].sum())

    pct = (
        round(wins / total * 100, 1)
        if total else 0
    )

    print()
    print(name)
    print("-" * 40)
    print("Kandidater:", total)
    print("Vinnare:", wins)
    print("Träff%:", pct)