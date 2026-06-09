import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[
    df["model_rank"].between(6, 8)
].copy()

tests = {
    "Odds < 5":
        rank68["avg_odds"] < 5,

    "Odds < 10":
        rank68["avg_odds"] < 10,

    "Odds < 15":
        rank68["avg_odds"] < 15,

    "Odds < 10 + Win% >= 25":
        (
            (rank68["avg_odds"] < 10)
            &
            (rank68["win_percent"] >= 25)
        ),

    "Odds < 10 + Spike >= 120":
        (
            (rank68["avg_odds"] < 10)
            &
            (
                rank68["win_percent"] * 2
                +
                rank68["form_score"] * 1.5
                +
                rank68["place_percent"]
            ) >= 120
        )
}

print("=" * 80)
print("RANK 6-8 ODDS")
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