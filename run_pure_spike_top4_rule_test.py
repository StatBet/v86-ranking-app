from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path("output/pure_spike_profiles_spike_rank_test")
RACES_FILE = BASE_DIR / "all_660_races_pure_spike.csv"
BASELINE_FILE = BASE_DIR / "pure_spike_hybrid_selected.csv"

OUTPUT_DIR = Path("output/pure_spike_top4_rule_test")
ADJUSTMENT_FILE = Path(
    "output/psv2_environment_analysis/"
    "leaf_bucket_adjustments_min8.csv"
)
TOP_N = 3

TOP_COMBOS = [
    ("P1", "P5A", "P5B"),
    ("P3", "P5A", "P5B"),
    ("P1", "P3", "P5A"),
    ("P1", "P3", "P5B"),
]

def apply_environment_calibration(
    races: pd.DataFrame,
) -> pd.DataFrame:

    out = races.copy()

    adjustments = pd.read_csv(
        ADJUSTMENT_FILE
    )

    adjustments = adjustments[
        [
            "rank1_environment_leaf_id",
            "pure_spike_score_bucket",
            "delta",
        ]
    ].copy()

    out = out.merge(
        adjustments,
        on=[
            "rank1_environment_leaf_id",
            "pure_spike_score_bucket",
        ],
        how="left",
    )

    out["delta"] = (
        numeric(out["delta"])
        .fillna(0)
    )

    out["adjusted_spike_percent"] = (
        numeric(out["adjusted_spike_percent"])
        + out["delta"]
    )

    return out

def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def make_race_key(df: pd.DataFrame) -> pd.Series:
    return (
        df["date"].astype(str)
        + "|"
        + df["track"].astype(str)
        + "|"
        + df["race_no"].astype(str)
    )


def build_signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["rank_spike_sum"] = (
        numeric(out["spike_score"])
        + numeric(out["total_score"])
    )

    out["spike_rank_advantage"] = (
        numeric(out["spike_score"])
        - numeric(out["total_score"])
    )

    out["P1"] = (
        (numeric(out["spike_score"]) >= 275)
        & (numeric(out["spike_score"]) < 375)
    )

    out["P2"] = (
        (numeric(out["spike_gap_1_2"]) >= 0)
        & (numeric(out["spike_gap_1_2"]) < 10)
    )

    out["P3"] = (
        (numeric(out["spike_score"]) >= 275)
        & (numeric(out["spike_score"]) < 375)
        & (numeric(out["spike_gap_1_2"]) >= 10)
        & (numeric(out["spike_gap_1_2"]) < 20)
        & (numeric(out["score_gap_1_2"]) >= 20)
        & (numeric(out["score_gap_1_2"]) < 30)
    )

    out["P4"] = numeric(out["total_score"]) >= 210

    out["P5A"] = (
        (numeric(out["rank_spike_sum"]) >= 550)
        & (numeric(out["rank_spike_sum"]) < 575)
    )

    out["P5B"] = (
        (numeric(out["spike_rank_advantage"]) >= 125)
        & (numeric(out["spike_rank_advantage"]) < 140)
    )

    return out


def calculate_signal_stats(
    races: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    for signal in ["P1", "P2", "P3", "P4", "P5A", "P5B"]:
        part = races[races[signal]]
        observations = len(part)
        winners = int(part["won"].sum())

        rows.append(
            {
                "signal": signal,
                "observations": observations,
                "winners": winners,
                "hit_rate_percent": (
                    winners / observations * 100
                    if observations
                    else 0.0
                ),
            }
        )

    return pd.DataFrame(rows)


def attach_combo_percent(
    races: pd.DataFrame,
    combo: tuple[str, ...],
    percent_map: dict[str, float],
    observations_map: dict[str, int],
) -> pd.DataFrame:
    out = races.copy()

    out["combo"] = "+".join(combo)
    out["combo_match_count"] = out[list(combo)].sum(axis=1)

    out["adjusted_spike_percent"] = numeric(
        out["pure_spike_percent"]
    ).fillna(0.0)

    out["adjusted_spike_observations"] = numeric(
        out["pure_spike_observations"]
    ).fillna(0).astype(int)

    out["matched_combo_rules"] = ""

    for signal in combo:
        mask = out[signal]

        stronger = (
            mask
            & (
                percent_map[signal]
                > out["adjusted_spike_percent"]
            )
        )

        out.loc[
            stronger,
            "adjusted_spike_percent",
        ] = percent_map[signal]

        out.loc[
            stronger,
            "adjusted_spike_observations",
        ] = observations_map[signal]

        current = out.loc[mask, "matched_combo_rules"]

        out.loc[
            mask,
            "matched_combo_rules",
        ] = current.where(
            current == "",
            current + "|",
        ) + signal

    return out


def build_candidates(
    races: pd.DataFrame,
) -> pd.DataFrame:
    spike = races.copy()
    spike["candidate_engine"] = "SPIKE"
    spike["candidate_percent"] = (
        spike["adjusted_spike_percent"]
    )
    spike["candidate_observations"] = (
        spike["adjusted_spike_observations"]
    )

    environment = races.copy()
    environment["candidate_engine"] = "ENVIRONMENT"
    environment["candidate_percent"] = numeric(
        environment["rank1_environment_adjusted_percent"]
    ).fillna(0.0)
    environment["candidate_observations"] = numeric(
        environment["rank1_environment_observations"]
    ).fillna(0).astype(int)

    candidates = pd.concat(
        [spike, environment],
        ignore_index=True,
    )

    return candidates.sort_values(
        [
            "date",
            "candidate_percent",
            "candidate_observations",
            "spike_score",
            "total_score",
            "race_no",
            "candidate_engine",
        ],
        ascending=[
            True,
            False,
            False,
            False,
            False,
            True,
            True,
        ],
        na_position="last",
    ).reset_index(drop=True)


def select_top3(
    candidates: pd.DataFrame,
) -> pd.DataFrame:
    selected_rows = []

    for date, round_candidates in candidates.groupby(
        "date",
        sort=True,
    ):
        used_races: set[str] = set()
        position = 0

        for _, candidate in round_candidates.iterrows():
            key = str(candidate["race_key"])

            if key in used_races:
                continue

            chosen = candidate.copy()
            position += 1
            chosen["hybrid_spike_position"] = position
            selected_rows.append(chosen)
            used_races.add(key)

            if position == TOP_N:
                break

        if position != TOP_N:
            raise ValueError(
                f"Omgång {date} gav bara {position} unika val."
            )

    return (
        pd.DataFrame(selected_rows)
        .sort_values(
            ["date", "hybrid_spike_position"]
        )
        .reset_index(drop=True)
    )


def analyze_result(
    baseline: pd.DataFrame,
    selected: pd.DataFrame,
) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    baseline_keys = set(baseline["race_key"])
    selected_keys = set(selected["race_key"])

    baseline_winner_keys = set(
        baseline.loc[
            baseline["won"] == 1,
            "race_key",
        ]
    )

    selected_winner_keys = set(
        selected.loc[
            selected["won"] == 1,
            "race_key",
        ]
    )

    true_new_keys = (
        selected_winner_keys - baseline_keys
    )

    lost_keys = (
        baseline_winner_keys - selected_keys
    )

    true_new = selected[
        selected["race_key"].isin(true_new_keys)
    ].copy()

    lost = baseline[
        baseline["race_key"].isin(lost_keys)
    ].copy()

    baseline_winners = int(
        baseline["won"].sum()
    )

    final_winners = int(
        selected["won"].sum()
    )

    metrics = {
        "baseline_winners": baseline_winners,
        "final_winners": final_winners,
        "true_new_winners": len(true_new_keys),
        "lost_baseline_winners": len(lost_keys),
        "preserved_baseline_winners": len(
            baseline_winner_keys & selected_keys
        ),
        "winner_gain": (
            final_winners - baseline_winners
        ),
        "changed_unique_races": len(
            baseline_keys.symmetric_difference(
                selected_keys
            )
        ),
    }

    return metrics, true_new, lost


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    races = pd.read_csv(RACES_FILE)
    baseline = pd.read_csv(BASELINE_FILE)

    required = {
        "date",
        "track",
        "race_no",
        "horse",
        "won",
        "spike_score",
        "total_score",
        "spike_gap_1_2",
        "score_gap_1_2",
        "pure_spike_percent",
        "pure_spike_observations",
        "rank1_environment_adjusted_percent",
        "rank1_environment_observations",
    }

    missing = sorted(
        required.difference(races.columns)
    )

    if missing:
        raise KeyError(
            "Loppfilen saknar: "
            + ", ".join(missing)
        )

    races["won"] = (
        numeric(races["won"])
        .fillna(0)
        .astype(int)
        .clip(0, 1)
    )

    baseline["won"] = (
        numeric(baseline["won"])
        .fillna(0)
        .astype(int)
        .clip(0, 1)
    )

    if "race_key" not in races.columns:
        races["race_key"] = make_race_key(races)

    if "race_key" not in baseline.columns:
        baseline["race_key"] = make_race_key(
            baseline
        )

    races = build_signals(races)

    signal_stats = calculate_signal_stats(
        races
    )

    percent_map = dict(
        zip(
            signal_stats["signal"],
            signal_stats["hit_rate_percent"],
        )
    )

    observations_map = dict(
        zip(
            signal_stats["signal"],
            signal_stats["observations"],
        )
    )

    summary_rows = []

    for combo in TOP_COMBOS:
        combo_name = "+".join(combo)
        combo_dir = OUTPUT_DIR / combo_name
        combo_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        adjusted = attach_combo_percent(
            races,
            combo,
            percent_map,
            observations_map,
        )

        adjusted = apply_environment_calibration(
            adjusted
        )

        candidates = build_candidates(
            adjusted
        )

        selected = select_top3(
            candidates
        )

        metrics, true_new, lost = analyze_result(
            baseline,
            selected,
        )

        summary_rows.append(
            {
                "combo": combo_name,
                "combo_size": len(combo),
                **metrics,
            }
        )

        adjusted.to_csv(
            combo_dir
            / "all_races_with_adjusted_percent.csv",
            index=False,
            encoding="utf-8-sig",
        )

        selected.to_csv(
            combo_dir
            / "selected_top3.csv",
            index=False,
            encoding="utf-8-sig",
        )

        true_new.to_csv(
            combo_dir
            / "true_new_winners.csv",
            index=False,
            encoding="utf-8-sig",
        )

        lost.to_csv(
            combo_dir
            / "lost_baseline_winners.csv",
            index=False,
            encoding="utf-8-sig",
        )

    summary = (
        pd.DataFrame(summary_rows)
        .sort_values(
            [
                "lost_baseline_winners",
                "winner_gain",
                "true_new_winners",
                "combo",
            ],
            ascending=[
                True,
                False,
                False,
                True,
            ],
        )
        .reset_index(drop=True)
    )

    signal_stats.to_csv(
        OUTPUT_DIR / "signal_statistics.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        OUTPUT_DIR / "top4_rule_test_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("=" * 130)
    print("PURE SPIKE – FYRA BÄSTA KOMBINATIONER")
    print("=" * 130)
    print()

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("Sparat i:")
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()