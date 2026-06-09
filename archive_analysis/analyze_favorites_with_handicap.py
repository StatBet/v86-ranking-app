import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

# Justera kolumnnamnet om du använder något annat
# ex handicap, tillagg, start_volt etc

print("=" * 80)
print("FAVORITER FRÅN TILLÄGG")
print("=" * 80)

favorites = df[df["model_rank"] == 1].copy()

# Anpassa denna rad efter din kolumn
favorites["is_tillagg"] = favorites["post"].isin(
    [6,7,8,9,10,11,12,13,14,15]
)

normal = favorites[~favorites["is_tillagg"]]
tillagg = favorites[favorites["is_tillagg"]]

print()
print("Favoriter utan tillägg")
print("-" * 40)
print("Antal:", len(normal))
print("Vinnare:", int(normal["won"].sum()))
print(
    "Träff%:",
    round(normal["won"].mean() * 100,1)
)

print()
print("Favoriter med tillägg")
print("-" * 40)
print("Antal:", len(tillagg))
print("Vinnare:", int(tillagg["won"].sum()))
print(
    "Träff%:",
    round(tillagg["won"].mean() * 100,1)
)