import pandas as pd

df = pd.read_csv("ml_dataset.csv")

bins = [
    0,
    400,
    500,
    600,
    700,
    800,
    900,
    99999
]

labels = [
    "<400",
    "400-500",
    "500-600",
    "600-700",
    "700-800",
    "800-900",
    "900+"
]

df["score_bucket"] = pd.cut(
    df["spike_score"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

summary = (
    df.groupby("score_bucket")
    .agg(
        horses=("won", "size"),
        winners=("won", "sum")
    )
    .reset_index()
)

summary["win_pct"] = (
    summary["winners"]
    / summary["horses"]
    * 100
).round(1)

print("=" * 80)
print("SPIKE SCORE BUCKETS")
print("=" * 80)

print(summary.to_string(index=False))

print()
print("=" * 80)
print("TOPP 100 HÖGSTA SPIKE SCORE")
print("=" * 80)

top100 = (
    df.sort_values(
        "spike_score",
        ascending=False
    )
    .head(100)
)

print(
    f"Hästar: {len(top100)}"
)

print(
    f"Vinnare: {top100['won'].sum()}"
)

print(
    f"Träff%: {round(top100['won'].mean()*100,1)}"
)

print()
print("=" * 80)
print("TOPP 50")
print("=" * 80)

top50 = (
    df.sort_values(
        "spike_score",
        ascending=False
    )
    .head(50)
)

print(
    f"Hästar: {len(top50)}"
)

print(
    f"Vinnare: {top50['won'].sum()}"
)

print(
    f"Träff%: {round(top50['won'].mean()*100,1)}"
)

print()
print("=" * 80)
print("TOPP 25")
print("=" * 80)

top25 = (
    df.sort_values(
        "spike_score",
        ascending=False
    )
    .head(25)
)

print(
    f"Hästar: {len(top25)}"
)

print(
    f"Vinnare: {top25['won'].sum()}"
)

print(
    f"Träff%: {round(top25['won'].mean()*100,1)}"
)