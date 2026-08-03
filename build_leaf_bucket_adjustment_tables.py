# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd

INPUT = Path(r"output\psv2_environment_analysis\leaf_bucket_adjustments.csv")
OUTPUT = Path(r"output\psv2_environment_analysis")

df = pd.read_csv(INPUT)

for minimum in [8,15]:

    out = (
        df[df["observations"] >= minimum]
        .copy()
        .sort_values(
            [
                "rank1_environment_leaf_id",
                "delta"
            ],
            ascending=[True,False]
        )
    )

    filename = f"leaf_bucket_adjustments_min{minimum}.csv"

    out.to_csv(
        OUTPUT / filename,
        index=False,
        encoding="utf-8-sig"
    )

    print("="*120)
    print(f"MINIMUM {minimum} OBSERVATIONER")
    print("="*120)
    print(out.to_string(index=False))
    print()

print("KLART")
print("Filer sparade i:")
print(OUTPUT)
