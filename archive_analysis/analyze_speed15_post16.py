import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

combo = df[
    (df["model_rank"].between(6,8))
    & (df["speed_score"] >= 20)
    & (df["post"].between(1,6))
]

print("="*80)
print("SPEED >=20 + POST 1-6")
print("="*80)

print()
print("Kandidater:", len(combo))
print("Vinnare:", int(combo["won"].sum()))

if len(combo):
    print(
        "Träff%",
        round(combo["won"].mean()*100,1)
    )

print()
print("Rank 6-8-vinnare:")

print(
    combo[combo["won"]==1][
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "speed_score",
            "post"
        ]
    ].to_string(index=False)
)