from pathlib import Path

import pandas as pd


HISTORICAL_FILE = Path("historical_rankings.csv")

LEAF_FILE = Path(
    r"output\psv2_environment_analysis\psv2_master_8_lopp.csv"
)

OUTPUT_DIR = Path(
    r"output\leaf_rank_distribution"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "leaf_rank_distribution.csv"
)


def normalize(df):
    out = df.copy()

    out["date"] = pd.to_numeric(
        out["date"],
        errors="coerce",
    ).astype("Int64")

    out["race_no"] = pd.to_numeric(
        out["race_no"],
        errors="coerce",
    ).astype("Int64")

    out["track"] = (
        out["track"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return out


def make_race_key(df):
    return (
        df["date"].astype(str)
        + "|"
        + df["track"].astype(str)
        + "|"
        + df["race_no"].astype(str)
    )


def rank_bucket(rank):
    rank = int(rank)

    if rank >= 10:
        return "10+"

    return str(rank)


historical = normalize(
    pd.read_csv(HISTORICAL_FILE)
)

leaf_data = normalize(
    pd.read_csv(LEAF_FILE)
)

historical["race_key"] = make_race_key(
    historical
)

leaf_data["race_key"] = make_race_key(
    leaf_data
)

historical["won"] = (
    pd.to_numeric(
        historical["won"],
        errors="coerce",
    )
    .fillna(0)
    .astype(int)
)

historical["model_rank"] = pd.to_numeric(
    historical["model_rank"],
    errors="coerce",
)

leaf_data["rank1_environment_leaf_id"] = (
    pd.to_numeric(
        leaf_data[
            "rank1_environment_leaf_id"
        ],
        errors="coerce",
    )
)

race_leaf = (
    leaf_data[
        [
            "race_key",
            "rank1_environment_leaf_id",
        ]
    ]
    .dropna(
        subset=[
            "rank1_environment_leaf_id"
        ]
    )
    .drop_duplicates(
        subset=["race_key"]
    )
)

winners = historical[
    historical["won"] == 1
].copy()

winners = winners.merge(
    race_leaf,
    on="race_key",
    how="inner",
    validate="many_to_one",
)

winners = winners.dropna(
    subset=[
        "model_rank",
        "rank1_environment_leaf_id",
    ]
)

winners["model_rank"] = (
    winners["model_rank"]
    .astype(int)
)

winners["leaf_id"] = (
    winners[
        "rank1_environment_leaf_id"
    ]
    .astype(int)
)

winners["rank_bucket"] = (
    winners["model_rank"]
    .apply(rank_bucket)
)

buckets = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10+",
]

rows = []

for leaf_id, group in winners.groupby(
    "leaf_id"
):
    observations = len(group)

    row = {
        "leaf_id": int(leaf_id),
        "observations": observations,
    }

    for bucket in buckets:
        count = int(
            (
                group["rank_bucket"]
                == bucket
            ).sum()
        )

        percent = (
            count / observations * 100
            if observations
            else 0
        )

        row[
            f"rank_{bucket}_winners"
        ] = count

        row[
            f"rank_{bucket}_percent"
        ] = round(
            percent,
            4,
        )

    rows.append(row)

result = pd.DataFrame(rows)

result = (
    result
    .sort_values(
        [
            "observations",
            "leaf_id",
        ],
        ascending=[
            False,
            True,
        ],
    )
    .reset_index(drop=True)
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

result.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig",
)

print("=" * 180)
print("EXAKT VINNARRANK PER LEAF")
print("=" * 180)
print()
print(result.to_string(index=False))
print()
print("Antal matchade lopp:", len(winners))
print("Sparat i:")
print(OUTPUT_FILE)