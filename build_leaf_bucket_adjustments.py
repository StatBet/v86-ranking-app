# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd

INPUT = Path(r"output\psv2_environment_analysis\psv2_master_8_lopp.csv")
OUTPUT = Path(r"output\psv2_environment_analysis")

df = pd.read_csv(INPUT)
df["won"] = pd.to_numeric(df["won"], errors="coerce").fillna(0).astype(int)

# -------------------------
# GLOBAL BUCKET
# -------------------------

global_bucket = (
    df.groupby("pure_spike_score_bucket")
      .agg(
          global_obs=("won","size"),
          global_wins=("won","sum")
      )
      .reset_index()
)

global_bucket["global_hit_rate"] = (
    100 * global_bucket["global_wins"] /
    global_bucket["global_obs"]
)

# -------------------------
# LEAF + BUCKET
# -------------------------

leaf_bucket = (
    df.groupby(
        [
            "rank1_environment_leaf_id",
            "pure_spike_score_bucket"
        ]
    )
    .agg(
        observations=("won","size"),
        winners=("won","sum")
    )
    .reset_index()
)

leaf_bucket["losers"] = (
    leaf_bucket["observations"] -
    leaf_bucket["winners"]
)

leaf_bucket["local_hit_rate"] = (
    100 * leaf_bucket["winners"] /
    leaf_bucket["observations"]
)

# -------------------------
# MERGE
# -------------------------

result = leaf_bucket.merge(
    global_bucket,
    on="pure_spike_score_bucket",
    how="left"
)

result["delta"] = (
    result["local_hit_rate"] -
    result["global_hit_rate"]
).round(2)

result = result.sort_values(
    [
        "rank1_environment_leaf_id",
        "delta"
    ],
    ascending=[True,False]
)

result.to_csv(
    OUTPUT / "leaf_bucket_adjustments.csv",
    index=False,
    encoding="utf-8-sig"
)

print("="*120)
print("LEAF BUCKET ADJUSTMENTS")
print("="*120)
print(result.to_string(index=False))

print()
print("Sparat i:")
print(OUTPUT / "leaf_bucket_adjustments.csv")

