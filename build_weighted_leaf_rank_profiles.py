from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    r"output\leaf_rank_distribution\leaf_rank_distribution.csv"
)

OUTPUT_DIR = Path(
    r"output\weighted_leaf_rank_profiles"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "weighted_leaf_rank_profiles.csv"
)

GROUPS = {
    "GROUP_5_10": [5, 10],
    "GROUP_8_19_20": [8, 19, 20],
}

RANK_BUCKETS = [
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


def percent_column(bucket: str) -> str:
    return f"rank_{bucket}_percent"


def winners_column(bucket: str) -> str:
    return f"rank_{bucket}_winners"


def get_leaf_row(
    df: pd.DataFrame,
    leaf_id: int,
) -> pd.Series:
    match = df[df["leaf_id"] == leaf_id]

    if match.empty:
        raise KeyError(
            f"Leaf {leaf_id} saknas i {INPUT_FILE}"
        )

    return match.iloc[0]


def build_group_profile(
    df: pd.DataFrame,
    leaf_ids: list[int],
) -> dict:
    group = df[df["leaf_id"].isin(leaf_ids)].copy()

    missing = sorted(
        set(leaf_ids) - set(group["leaf_id"].astype(int))
    )

    if missing:
        raise KeyError(
            "Följande leafs saknas: "
            + ", ".join(map(str, missing))
        )

    observations = int(group["observations"].sum())

    profile = {
        "observations": observations,
    }

    for bucket in RANK_BUCKETS:
        winners = int(
            group[winners_column(bucket)].sum()
        )

        profile[f"rank_{bucket}_winners"] = winners
        profile[f"rank_{bucket}_percent"] = (
            winners / observations * 100
            if observations
            else 0.0
        )

    return profile


def build_global_profile(
    df: pd.DataFrame,
) -> dict:
    observations = int(df["observations"].sum())

    profile = {
        "observations": observations,
    }

    for bucket in RANK_BUCKETS:
        winners = int(
            df[winners_column(bucket)].sum()
        )

        profile[f"rank_{bucket}_winners"] = winners
        profile[f"rank_{bucket}_percent"] = (
            winners / observations * 100
            if observations
            else 0.0
        )

    return profile


def weighted_leaf_profile(
    leaf_row: pd.Series,
    group_profile: dict,
) -> dict:
    leaf_observations = int(
        leaf_row["observations"]
    )
    group_observations = int(
        group_profile["observations"]
    )

    leaf_weight = (
        leaf_observations / group_observations
        if group_observations
        else 0.0
    )
    group_weight = 1.0 - leaf_weight

    profile = {
        "leaf_observations": leaf_observations,
        "group_observations": group_observations,
        "leaf_weight": leaf_weight,
        "group_weight": group_weight,
    }

    for bucket in RANK_BUCKETS:
        leaf_percent = float(
            leaf_row[percent_column(bucket)]
        )
        group_percent = float(
            group_profile[
                f"rank_{bucket}_percent"
            ]
        )

        weighted_percent = (
            leaf_percent * leaf_weight
            + group_percent * group_weight
        )

        profile[
            f"rank_{bucket}_raw_percent"
        ] = leaf_percent

        profile[
            f"rank_{bucket}_group_percent"
        ] = group_percent

        profile[
            f"rank_{bucket}_weighted_percent"
        ] = weighted_percent

    return profile


def add_final_grouped_percentages(
    row: dict,
) -> dict:
    row["rank_2_final_percent"] = row[
        "rank_2_weighted_percent"
    ]
    row["rank_3_final_percent"] = row[
        "rank_3_weighted_percent"
    ]
    row["rank_4_final_percent"] = row[
        "rank_4_weighted_percent"
    ]
    row["rank_5_final_percent"] = row[
        "rank_5_weighted_percent"
    ]

    rank_6_7_pool = (
        row["rank_6_weighted_percent"]
        + row["rank_7_weighted_percent"]
    )
    row["rank_6_7_pool_percent"] = rank_6_7_pool
    row["rank_6_7_each_percent"] = (
        rank_6_7_pool / 2
    )

    rank_8_9_pool = (
        row["rank_8_weighted_percent"]
        + row["rank_9_weighted_percent"]
    )
    row["rank_8_9_pool_percent"] = rank_8_9_pool
    row["rank_8_9_each_percent"] = (
        rank_8_9_pool / 2
    )

    row["rank_10_plus_pool_percent"] = row[
        "rank_10+_weighted_percent"
    ]

    row["rank_2_plus_total_percent"] = sum(
        row[f"rank_{bucket}_weighted_percent"]
        for bucket in RANK_BUCKETS
        if bucket != "1"
    )

    return row


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Hittar inte filen: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    df["leaf_id"] = pd.to_numeric(
        df["leaf_id"],
        errors="raise",
    ).astype(int)

    df["observations"] = pd.to_numeric(
        df["observations"],
        errors="raise",
    ).astype(int)

    for bucket in RANK_BUCKETS:
        df[winners_column(bucket)] = pd.to_numeric(
            df[winners_column(bucket)],
            errors="raise",
        ).astype(int)

        df[percent_column(bucket)] = pd.to_numeric(
            df[percent_column(bucket)],
            errors="raise",
        ).astype(float)

    group_5_10 = build_group_profile(
        df,
        GROUPS["GROUP_5_10"],
    )

    group_8_19_20 = build_group_profile(
        df,
        GROUPS["GROUP_8_19_20"],
    )

    global_profile = build_global_profile(df)

    rows = []

    leaf_4 = get_leaf_row(df, 4)

    raw_4 = {
        "profile_key": "LEAF_4",
        "leaf_id": 4,
        "profile_type": "RAW_LEAF",
        "group_key": "LEAF_4",
        "leaf_observations": int(
            leaf_4["observations"]
        ),
        "group_observations": int(
            leaf_4["observations"]
        ),
        "leaf_weight": 1.0,
        "group_weight": 0.0,
    }

    for bucket in RANK_BUCKETS:
        value = float(
            leaf_4[percent_column(bucket)]
        )

        raw_4[
            f"rank_{bucket}_raw_percent"
        ] = value
        raw_4[
            f"rank_{bucket}_group_percent"
        ] = value
        raw_4[
            f"rank_{bucket}_weighted_percent"
        ] = value

    rows.append(
        add_final_grouped_percentages(raw_4)
    )

    for leaf_id in [5, 10]:
        leaf_row = get_leaf_row(df, leaf_id)

        row = {
            "profile_key": f"LEAF_{leaf_id}",
            "leaf_id": leaf_id,
            "profile_type": "WEIGHTED_LEAF",
            "group_key": "GROUP_5_10",
        }

        row.update(
            weighted_leaf_profile(
                leaf_row,
                group_5_10,
            )
        )

        rows.append(
            add_final_grouped_percentages(row)
        )

    for leaf_id in [8, 19, 20]:
        leaf_row = get_leaf_row(df, leaf_id)

        row = {
            "profile_key": f"LEAF_{leaf_id}",
            "leaf_id": leaf_id,
            "profile_type": "WEIGHTED_LEAF",
            "group_key": "GROUP_8_19_20",
        }

        row.update(
            weighted_leaf_profile(
                leaf_row,
                group_8_19_20,
            )
        )

        rows.append(
            add_final_grouped_percentages(row)
        )

    global_row = {
        "profile_key": "GLOBAL",
        "leaf_id": "",
        "profile_type": "GLOBAL",
        "group_key": "GLOBAL_660",
        "leaf_observations": int(
            global_profile["observations"]
        ),
        "group_observations": int(
            global_profile["observations"]
        ),
        "leaf_weight": 1.0,
        "group_weight": 0.0,
    }

    for bucket in RANK_BUCKETS:
        value = float(
            global_profile[
                f"rank_{bucket}_percent"
            ]
        )

        global_row[
            f"rank_{bucket}_raw_percent"
        ] = value
        global_row[
            f"rank_{bucket}_group_percent"
        ] = value
        global_row[
            f"rank_{bucket}_weighted_percent"
        ] = value

    rows.append(
        add_final_grouped_percentages(
            global_row
        )
    )

    result = pd.DataFrame(rows)

    numeric_columns = result.select_dtypes(
        include="number"
    ).columns

    result[numeric_columns] = (
        result[numeric_columns].round(4)
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

    display_columns = [
        "profile_key",
        "group_key",
        "leaf_observations",
        "group_observations",
        "leaf_weight",
        "group_weight",
        "rank_2_final_percent",
        "rank_3_final_percent",
        "rank_4_final_percent",
        "rank_5_final_percent",
        "rank_6_7_pool_percent",
        "rank_6_7_each_percent",
        "rank_8_9_pool_percent",
        "rank_8_9_each_percent",
        "rank_10_plus_pool_percent",
        "rank_2_plus_total_percent",
    ]

    print("=" * 190)
    print(
        "VIKTADE LEAF-PROFILER – RANK 2+"
    )
    print(
        "Rank 1 styrs av hybridmotorn och används inte här."
    )
    print("=" * 190)
    print()
    print(
        result[display_columns].to_string(
            index=False
        )
    )
    print()
    print("Sparat i:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()