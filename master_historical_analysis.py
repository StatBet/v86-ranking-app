import json
from pathlib import Path

import pandas as pd


INPUT_FILE = Path("historical_rankings.csv")
OUTPUT_DIR = Path("master_analysis_output")

OUTPUT_DIR.mkdir(exist_ok=True)


def pct(numerator, denominator):
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


def numeric(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


def save_csv(df, filename):
    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def validate_input(df):
    required = {
        "race_id",
        "won",
        "model_rank",
        "total_score",
        "spike_score",
        "spread",
        "percent",
    }

    missing = sorted(required - set(df.columns))

    if missing:
        raise ValueError(
            "Saknade obligatoriska kolumner: "
            + ", ".join(missing)
        )


def prepare_data(df):
    df = df.copy()

    numeric_columns = [
        "won",
        "model_rank",
        "total_score",
        "spike_score",
        "spread",
        "percent",
        "number",
        "race_no",
        "win_score",
        "form_score",
        "latest_start_score",
        "place_score",
        "speed_score",
        "post",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = numeric(df[column])

    winner_counts = df.groupby("race_id")["won"].sum()
    valid_race_ids = winner_counts[winner_counts == 1].index

    valid = df[df["race_id"].isin(valid_race_ids)].copy()
    winners = valid[valid["won"] == 1].copy()

    return valid, winners, winner_counts


def ranking_summary(valid, winners):
    races = winners["race_id"].nunique()

    row = {
        "valid_races": races,
        "horses": len(valid),
        "avg_field_size": round(
            valid.groupby("race_id").size().mean(),
            3,
        ),
        "avg_winner_rank": round(
            winners["model_rank"].mean(),
            3,
        ),
        "median_winner_rank": round(
            winners["model_rank"].median(),
            3,
        ),
    }

    for top in range(1, 9):
        hits = int((winners["model_rank"] <= top).sum())
        row[f"top{top}"] = hits
        row[f"top{top}_pct"] = pct(hits, races)

    return pd.DataFrame([row])


def winner_rank_distribution(winners):
    distribution = (
        winners.groupby("model_rank")
        .size()
        .reset_index(name="winners")
        .sort_values("model_rank")
    )

    total = len(winners)
    distribution["winner_pct"] = distribution["winners"].apply(
        lambda value: pct(value, total)
    )
    distribution["cumulative_winners"] = distribution["winners"].cumsum()
    distribution["cumulative_pct"] = distribution[
        "cumulative_winners"
    ].apply(lambda value: pct(value, total))

    return distribution


def race_level_data(valid):
    rows = []

    for race_id, group in valid.groupby("race_id"):
        ordered = group.sort_values(
            ["model_rank", "total_score"],
            ascending=[True, False],
        )

        winner = group[group["won"] == 1].iloc[0]

        row = {
            "race_id": race_id,
            "date": winner.get("date", ""),
            "race_no": winner.get("race_no", 0),
            "track": winner.get("track", ""),
            "field_size": len(group),
            "winner": winner.get("horse", ""),
            "winner_number": winner.get("number", 0),
            "winner_rank": winner.get("model_rank", 0),
            "winner_total_score": winner.get("total_score", 0),
            "winner_spike_score": winner.get("spike_score", 0),
            "winner_percent": winner.get("percent", 0),
            "spread": group["spread"].iloc[0],
            "rank1_total_score": (
                ordered.iloc[0]["total_score"]
                if len(ordered) >= 1 else 0
            ),
            "rank2_total_score": (
                ordered.iloc[1]["total_score"]
                if len(ordered) >= 2 else 0
            ),
            "rank1_spike_score": (
                ordered.iloc[0]["spike_score"]
                if len(ordered) >= 1 else 0
            ),
            "rank2_spike_score": (
                ordered.iloc[1]["spike_score"]
                if len(ordered) >= 2 else 0
            ),
            "total_sum": round(group["total_score"].sum(), 3),
            "spike_sum": round(group["spike_score"].sum(), 3),
        }

        row["score_gap_1_2"] = round(
            row["rank1_total_score"] - row["rank2_total_score"],
            3,
        )

        row["spike_gap_1_2"] = round(
            row["rank1_spike_score"] - row["rank2_spike_score"],
            3,
        )

        rows.append(row)

    return pd.DataFrame(rows)


def race_bucket_summary(races, column, bins, labels):
    temp = races.copy()
    temp["bucket"] = pd.cut(
        temp[column],
        bins=bins,
        labels=labels,
        include_lowest=True,
        right=True,
    )

    rows = []

    for bucket, group in temp.groupby("bucket", observed=False):
        if group.empty:
            continue

        total = len(group)

        row = {
            "bucket": str(bucket),
            "races": total,
            "avg_field_size": round(group["field_size"].mean(), 3),
            "avg_winner_rank": round(group["winner_rank"].mean(), 3),
            "avg_winner_percent": round(
                group["winner_percent"].mean(),
                3,
            ),
        }

        for top in range(1, 6):
            hits = int((group["winner_rank"] <= top).sum())
            row[f"top{top}"] = hits
            row[f"top{top}_pct"] = pct(hits, total)

        rows.append(row)

    return pd.DataFrame(rows)


def horse_bucket_summary(valid, column, bins, labels):
    temp = valid.copy()
    temp["bucket"] = pd.cut(
        temp[column],
        bins=bins,
        labels=labels,
        include_lowest=True,
        right=True,
    )

    rows = []

    for bucket, group in temp.groupby("bucket", observed=False):
        if group.empty:
            continue

        horses = len(group)
        winners = int(group["won"].sum())

        rows.append({
            "bucket": str(bucket),
            "horses": horses,
            "winners": winners,
            "winner_pct": pct(winners, horses),
            "avg_model_rank": round(
                group["model_rank"].mean(),
                3,
            ),
            "avg_percent": round(
                group["percent"].mean(),
                3,
            ),
        })

    return pd.DataFrame(rows)


def rank_zone_summary(valid):
    rows = []

    zones = [
        ("Rank 1", 1, 1),
        ("Rank 2", 2, 2),
        ("Rank 3", 3, 3),
        ("Rank 1-3", 1, 3),
        ("Rank 4-5", 4, 5),
        ("Rank 4-7", 4, 7),
        ("Rank 6+", 6, 999),
    ]

    for label, low, high in zones:
        group = valid[
            valid["model_rank"].between(low, high)
        ]

        horses = len(group)
        winners = int(group["won"].sum())

        rows.append({
            "zone": label,
            "horses": horses,
            "winners": winners,
            "winner_pct": pct(winners, horses),
            "avg_total_score": round(
                group["total_score"].mean(),
                3,
            ) if horses else 0,
            "avg_spike_score": round(
                group["spike_score"].mean(),
                3,
            ) if horses else 0,
            "avg_percent": round(
                group["percent"].mean(),
                3,
            ) if horses else 0,
        })

    return pd.DataFrame(rows)


def low_percent_summary(valid):
    rows = []

    rules = [
        ("<=5%", 0, 5),
        ("<=10%", 0, 10),
        ("5-10%", 5, 10),
        ("<=15%", 0, 15),
        ("<=20%", 0, 20),
    ]

    for label, low, high in rules:
        if low == 0:
            group = valid[valid["percent"] <= high]
        else:
            group = valid[
                valid["percent"].between(low, high)
            ]

        horses = len(group)
        winners = int(group["won"].sum())

        rows.append({
            "percent_group": label,
            "horses": horses,
            "winners": winners,
            "winner_pct": pct(winners, horses),
            "avg_rank": round(
                group["model_rank"].mean(),
                3,
            ) if horses else 0,
            "avg_total_score": round(
                group["total_score"].mean(),
                3,
            ) if horses else 0,
            "avg_spike_score": round(
                group["spike_score"].mean(),
                3,
            ) if horses else 0,
        })

    return pd.DataFrame(rows)


def value_candidate_summary(valid):
    rules = [
        {
            "rule": "Rank 3-5 | Score 125-134 | Spike >=105",
            "mask": (
                valid["model_rank"].between(3, 5)
                & valid["total_score"].between(125, 134)
                & (valid["spike_score"] >= 105)
            ),
        },
        {
            "rule": "Rank 4-7 | Score 125-134 | Spike >=105",
            "mask": (
                valid["model_rank"].between(4, 7)
                & valid["total_score"].between(125, 134)
                & (valid["spike_score"] >= 105)
            ),
        },
        {
            "rule": "Rank 3-5 | Score 120-139 | Spike >=125",
            "mask": (
                valid["model_rank"].between(3, 5)
                & valid["total_score"].between(120, 139)
                & (valid["spike_score"] >= 125)
            ),
        },
        {
            "rule": "Rank 4-7 | Score 120-139 | Spike >=120 | <=20%",
            "mask": (
                valid["model_rank"].between(4, 7)
                & valid["total_score"].between(120, 139)
                & (valid["spike_score"] >= 120)
                & (valid["percent"] <= 20)
            ),
        },
    ]

    rows = []

    for item in rules:
        group = valid[item["mask"]]
        horses = len(group)
        winners = int(group["won"].sum())

        rows.append({
            "rule": item["rule"],
            "candidates": horses,
            "winners": winners,
            "winner_pct": pct(winners, horses),
            "races": group["race_id"].nunique(),
            "avg_candidates_per_race": round(
                horses / group["race_id"].nunique(),
                3,
            ) if group["race_id"].nunique() else 0,
            "avg_rank": round(
                group["model_rank"].mean(),
                3,
            ) if horses else 0,
            "avg_percent": round(
                group["percent"].mean(),
                3,
            ) if horses else 0,
        })

    return pd.DataFrame(rows)


def badge_summary(valid):
    if "badges" not in valid.columns:
        return pd.DataFrame()

    rows = []

    for _, row in valid.iterrows():
        raw = str(row.get("badges", "") or "").strip()

        if not raw or raw == "0":
            continue

        badges = [
            badge.strip()
            for badge in raw.split("|")
            if badge.strip()
        ]

        for badge in badges:
            rows.append({
                "badge": badge,
                "race_id": row["race_id"],
                "won": row["won"],
                "model_rank": row["model_rank"],
                "percent": row["percent"],
            })

    if not rows:
        return pd.DataFrame()

    exploded = pd.DataFrame(rows)
    summary_rows = []

    for badge, group in exploded.groupby("badge"):
        candidates = len(group)
        winners = int(group["won"].sum())

        summary_rows.append({
            "badge": badge,
            "candidates": candidates,
            "winners": winners,
            "winner_pct": pct(winners, candidates),
            "races": group["race_id"].nunique(),
            "avg_rank": round(
                group["model_rank"].mean(),
                3,
            ),
            "avg_percent": round(
                group["percent"].mean(),
                3,
            ),
        })

    return pd.DataFrame(summary_rows).sort_values(
        ["winner_pct", "candidates"],
        ascending=[True, False],
    )


def track_summary(races):
    rows = []

    for track, group in races.groupby("track"):
        if not track or str(track) == "0":
            continue

        total = len(group)

        rows.append({
            "track": track,
            "races": total,
            "avg_field_size": round(
                group["field_size"].mean(),
                3,
            ),
            "top1_pct": pct(
                int((group["winner_rank"] <= 1).sum()),
                total,
            ),
            "top3_pct": pct(
                int((group["winner_rank"] <= 3).sum()),
                total,
            ),
            "top5_pct": pct(
                int((group["winner_rank"] <= 5).sum()),
                total,
            ),
            "avg_winner_rank": round(
                group["winner_rank"].mean(),
                3,
            ),
        })

    return pd.DataFrame(rows).sort_values(
        "races",
        ascending=False,
    )


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Hittar inte {INPUT_FILE}. Kör build_historical_rankings.py först."
        )

    df = pd.read_csv(INPUT_FILE)
    validate_input(df)

    valid, winners, winner_counts = prepare_data(df)

    ranking_df = ranking_summary(valid, winners)
    winner_distribution_df = winner_rank_distribution(winners)
    races_df = race_level_data(valid)

    spread_df = race_bucket_summary(
        races_df,
        "spread",
        bins=[
            float("-inf"),
            49,
            59,
            69,
            74,
            79,
            89,
            float("inf"),
        ],
        labels=[
            "<=49",
            "50-59",
            "60-69",
            "70-74",
            "75-79",
            "80-89",
            "90+",
        ],
    )

    total_sum_df = race_bucket_summary(
        races_df,
        "total_sum",
        bins=[
            float("-inf"),
            999,
            1099,
            1199,
            1299,
            1399,
            1499,
            1599,
            float("inf"),
        ],
        labels=[
            "<=999",
            "1000-1099",
            "1100-1199",
            "1200-1299",
            "1300-1399",
            "1400-1499",
            "1500-1599",
            "1600+",
        ],
    )

    spike_sum_df = race_bucket_summary(
        races_df,
        "spike_sum",
        bins=[
            float("-inf"),
            599,
            799,
            999,
            1199,
            1399,
            float("inf"),
        ],
        labels=[
            "<=599",
            "600-799",
            "800-999",
            "1000-1199",
            "1200-1399",
            "1400+",
        ],
    )

    total_score_df = horse_bucket_summary(
        valid,
        "total_score",
        bins=[
            float("-inf"),
            79,
            99,
            119,
            139,
            159,
            179,
            199,
            float("inf"),
        ],
        labels=[
            "<=79",
            "80-99",
            "100-119",
            "120-139",
            "140-159",
            "160-179",
            "180-199",
            "200+",
        ],
    )

    spike_score_df = horse_bucket_summary(
        valid,
        "spike_score",
        bins=[
            float("-inf"),
            99,
            124,
            149,
            174,
            199,
            224,
            249,
            float("inf"),
        ],
        labels=[
            "<=99",
            "100-124",
            "125-149",
            "150-174",
            "175-199",
            "200-224",
            "225-249",
            "250+",
        ],
    )

    rank_zone_df = rank_zone_summary(valid)
    low_percent_df = low_percent_summary(valid)
    value_df = value_candidate_summary(valid)
    badges_df = badge_summary(valid)
    tracks_df = track_summary(races_df)

    invalid_races = winner_counts[winner_counts != 1]

    saved = []

    saved.append(save_csv(ranking_df, "01_ranking_summary.csv"))
    saved.append(save_csv(
        winner_distribution_df,
        "02_winner_rank_distribution.csv",
    ))
    saved.append(save_csv(races_df, "03_race_level_data.csv"))
    saved.append(save_csv(spread_df, "04_spread_buckets.csv"))
    saved.append(save_csv(total_sum_df, "05_total_sum_buckets.csv"))
    saved.append(save_csv(spike_sum_df, "06_spike_sum_buckets.csv"))
    saved.append(save_csv(total_score_df, "07_total_score_buckets.csv"))
    saved.append(save_csv(spike_score_df, "08_spike_score_buckets.csv"))
    saved.append(save_csv(rank_zone_df, "09_rank_zones.csv"))
    saved.append(save_csv(low_percent_df, "10_low_percent_groups.csv"))
    saved.append(save_csv(value_df, "11_value_candidate_rules.csv"))
    saved.append(save_csv(tracks_df, "12_track_summary.csv"))

    if not badges_df.empty:
        saved.append(save_csv(badges_df, "13_badge_summary.csv"))

    invalid_df = invalid_races.reset_index()
    invalid_df.columns = ["race_id", "winner_count"]
    saved.append(save_csv(invalid_df, "14_invalid_winner_matches.csv"))

    metadata = {
        "input_file": str(INPUT_FILE),
        "all_rows": int(len(df)),
        "all_races": int(df["race_id"].nunique()),
        "valid_races": int(valid["race_id"].nunique()),
        "invalid_races": int(len(invalid_df)),
        "matched_winners": int(valid["won"].sum()),
        "columns": list(df.columns),
    }

    metadata_path = OUTPUT_DIR / "00_metadata.json"
    metadata_path.write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    saved.insert(0, metadata_path)

    print("=" * 120)
    print("MASTERANALYS - HISTORISK RANKING")
    print("=" * 120)
    print()
    print(f"Alla rader:          {len(df)}")
    print(f"Alla lopp:           {df['race_id'].nunique()}")
    print(f"Giltiga lopp:        {valid['race_id'].nunique()}")
    print(f"Ogiltiga lopp:       {len(invalid_df)}")
    print(f"Matchade vinnare:    {int(valid['won'].sum())}")
    print()
    print("-" * 120)
    print("RANKING")
    print("-" * 120)
    print(ranking_df.to_string(index=False))
    print()
    print("-" * 120)
    print("SPREAD - PER LOPP")
    print("-" * 120)
    print(spread_df.to_string(index=False))
    print()
    print("-" * 120)
    print("RANKZONER")
    print("-" * 120)
    print(rank_zone_df.to_string(index=False))
    print()
    print("-" * 120)
    print("VALUE-REGLER")
    print("-" * 120)
    print(value_df.to_string(index=False))
    print()

    if not badges_df.empty:
        print("-" * 120)
        print("BADGES")
        print("-" * 120)
        print(badges_df.to_string(index=False))
        print()

    print("Sparat i mappen:")
    print(OUTPUT_DIR)

    for path in saved:
        print(path)


if __name__ == "__main__":
    main()