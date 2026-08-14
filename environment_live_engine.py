from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import copy

import joblib
import numpy as np
import pandas as pd

# ============================================================
# LIVE RACE-FEATURE BUILDER
#
# Självbärande kopia av exakt den featurelogik som användes
# för Environment V2 BUILD-master.
# Ingen extern analysfil krävs i Streamlit.
# ============================================================

def _num_series(series):
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def _safe_value(row, key, default=np.nan):

    if key not in row.index:
        return default

    value = row.get(
        key,
        default,
    )

    # Live kan innehålla listor, t.ex. badges.
    if isinstance(
        value,
        (list, tuple, set),
    ):
        return " | ".join(
            str(item)
            for item in value
        )

    try:
        missing = pd.isna(
            value
        )

        if isinstance(
            missing,
            (bool, np.bool_),
        ) and missing:
            return default

    except Exception:
        pass

    return value


def _get_ranked(race):

    race = race.copy()

    if "model_rank" in race.columns:

        race[
            "model_rank"
        ] = pd.to_numeric(
            race[
                "model_rank"
            ],
            errors="coerce",
        )

        race = (
            race
            .sort_values(
                "model_rank",
                ascending=True,
                kind="stable",
            )
            .reset_index(
                drop=True
            )
        )

    else:

        race = race.reset_index(
            drop=True
        )

    return race


def _at_rank(
    race,
    column,
    rank,
):

    if column not in race.columns:
        return np.nan

    index = (
        rank - 1
    )

    if (
        index < 0
        or index >= len(race)
    ):
        return np.nan

    return pd.to_numeric(
        pd.Series(
            [
                race.iloc[
                    index
                ].get(
                    column,
                    np.nan,
                )
            ]
        ),
        errors="coerce",
    ).iloc[0]


def _score_spread(
    race,
    column,
    target_rank,
):

    if (
        column not in race.columns
        or len(race) < target_rank
    ):
        return np.nan

    first = _at_rank(
        race,
        column,
        1,
    )

    target = _at_rank(
        race,
        column,
        target_rank,
    )

    if (
        pd.isna(first)
        or pd.isna(target)
    ):
        return np.nan

    return (
        first
        - target
    )


def _series_stats(
    race,
    column,
    prefix,
):

    if column not in race.columns:
        return {}

    series = (
        _num_series(
            race[column]
        )
        .dropna()
    )

    if series.empty:
        return {}

    return {
        f"{prefix}_sum":
            series.sum(),

        f"{prefix}_mean":
            series.mean(),

        f"{prefix}_median":
            series.median(),

        f"{prefix}_std":
            series.std(
                ddof=0
            ),

        f"{prefix}_max":
            series.max(),

        f"{prefix}_min":
            series.min(),

        f"{prefix}_range":
            (
                series.max()
                - series.min()
            ),
    }


def make_race_row(
    date,
    race_no,
    race,
):

    race = _get_ranked(
        race
    )

    if race.empty:
        return {}

    rank1 = race.iloc[0]

    race_id = (
        str(
            _safe_value(
                rank1,
                "race_id",
                "",
            )
        )
        if "race_id"
        in race.columns
        else ""
    )

    if (
        not race_id
        or race_id == "nan"
    ):
        race_id = (
            f"{int(date)}_"
            f"{int(race_no)}"
        )

    row = {
        "date":
            int(date),

        "race_no":
            int(race_no),

        "race_id":
            race_id,

        "track":
            _safe_value(
                rank1,
                "track",
                "",
            ),

        "race_type":
            _safe_value(
                rank1,
                "race_type",
                "",
            ),

        "start_type":
            _safe_value(
                rank1,
                "start_type",
                "",
            ),

        "distance":
            _safe_value(
                rank1,
                "distance",
                np.nan,
            ),

        "field_size":
            len(race),

        "rank1_total":
            _at_rank(
                race,
                "total_score",
                1,
            ),

        "rank2_total":
            _at_rank(
                race,
                "total_score",
                2,
            ),

        "rank3_total":
            _at_rank(
                race,
                "total_score",
                3,
            ),

        "rank4_total":
            _at_rank(
                race,
                "total_score",
                4,
            ),

        "rank5_total":
            _at_rank(
                race,
                "total_score",
                5,
            ),

        "rank1_spike":
            _at_rank(
                race,
                "spike_score",
                1,
            ),

        "rank2_spike":
            _at_rank(
                race,
                "spike_score",
                2,
            ),

        "rank3_spike":
            _at_rank(
                race,
                "spike_score",
                3,
            ),

        "score_gap_1_2":
            _score_spread(
                race,
                "total_score",
                2,
            ),

        "score_gap_1_3":
            _score_spread(
                race,
                "total_score",
                3,
            ),

        "score_gap_1_4":
            _score_spread(
                race,
                "total_score",
                4,
            ),

        "score_gap_1_5":
            _score_spread(
                race,
                "total_score",
                5,
            ),

        "spread_1_8":
            _score_spread(
                race,
                "total_score",
                8,
            ),

        "spike_gap_1_2":
            _score_spread(
                race,
                "spike_score",
                2,
            ),

        "spike_gap_1_3":
            _score_spread(
                race,
                "spike_score",
                3,
            ),

        "spike_gap_1_4":
            _score_spread(
                race,
                "spike_score",
                4,
            ),
    }

    row.update(
        _series_stats(
            race,
            "total_score",
            "total",
        )
    )

    row.update(
        _series_stats(
            race,
            "spike_score",
            "spike",
        )
    )

    score_columns = [
        "speed_score",
        "latest_start_score",
        "form_score",
        "stallform_score",
        "post_score",
        "driver_score",
        "driver_change_score",
        "record_score",
        "starts_score",
        "win_score",
        "place_score",
        "spel_score",
        "prize_money_score",
        "recent_prize_score",
        "class_change_score",
        "avg_odds_score",
        "wagon_score",
        "shoe_score",
        "inactivity_score",
        "custom_score",
        "distance_addition_score",
        "gender_score",
        "gallop_score",
        "start_points",
        "eps_value",
    ]

    for column in score_columns:

        if column not in race.columns:
            continue

        series = (
            _num_series(
                race[column]
            )
            .dropna()
        )

        if series.empty:
            continue

        row[
            f"{column}_mean"
        ] = series.mean()

        row[
            f"{column}_max"
        ] = series.max()

        row[
            f"{column}_min"
        ] = series.min()

        row[
            f"{column}_range"
        ] = (
            series.max()
            - series.min()
        )

        row[
            f"rank1_{column}"
        ] = _at_rank(
            race,
            column,
            1,
        )

    # Dessa följer endast med som auditfält.
    for column in (
        "loppbadge",
        "loppbadge_x",
        "loppbadge_y",
        "badges",
    ):

        if column in race.columns:

            row[
                column
            ] = _safe_value(
                rank1,
                column,
                "",
            )

    return row

MODEL_FILE = Path(
    "config/environment_model_v2_frozen.joblib"
)

VERSION_EXPECTED = (
    "ENVIRONMENT_V2_BUILD81_FROZEN_20260814"
)


ENVIRONMENT_ICONS = {
    "Favoritrank": "⭐",
    "Solid": "🟢",
    "Neutral": "⚪",
    "Öppet": "🟡",
    "Kaos": "🔴",
    "Extrem kaos": "💥",
    "UT": "⚫",
}


def _safe_int(value, default=0):
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


@lru_cache(maxsize=1)
def load_environment_model():

    if not MODEL_FILE.exists():
        raise RuntimeError(
            "Fryst miljömodell saknas: "
            f"{MODEL_FILE}"
        )

    bundle = joblib.load(
        MODEL_FILE
    )

    version = bundle.get(
        "version",
        "",
    )

    if version != VERSION_EXPECTED:
        raise RuntimeError(
            "Fel miljömodellversion. "
            f"Förväntad={VERSION_EXPECTED}, "
            f"hittad={version}"
        )

    required = {
        "pipeline",
        "features",
        "categorical",
        "numeric",
        "medians",
        "leaf_to_environment",
        "environment_profiles",
    }

    missing = (
        required
        - set(bundle)
    )

    if missing:
        raise RuntimeError(
            "Fryst miljömodell saknar: "
            + ", ".join(
                sorted(missing)
            )
        )

    return bundle


def _prepare_race_frame(
    race_data: dict,
    order: list[dict],
) -> pd.DataFrame:

    race = race_data.get(
        "race",
        {},
    )

    date = _safe_int(
        race.get(
            "date",
            race.get(
                "race_date",
                0,
            ),
        ),
        0,
    )

    race_no = _safe_int(
        race.get(
            "race_no",
            0,
        ),
        0,
    )

    rows = []

    for rank, horse in enumerate(
        order,
        start=1,
    ):
        row = copy.copy(
            horse
        )

        # make_race_row använder model_rank
        # som fysisk ordning.
        row["model_rank"] = rank

        # Liveinformationen ligger huvudsakligen
        # i race_data["race"]. Historiska master-
        # filen hade dessa även på hästraden.
        row.setdefault(
            "date",
            date,
        )

        row.setdefault(
            "race_no",
            race_no,
        )

        row.setdefault(
            "track",
            race.get(
                "track",
                "",
            ),
        )

        row.setdefault(
            "distance",
            race.get(
                "distance",
                np.nan,
            ),
        )

        row.setdefault(
            "race_type",
            race.get(
                "race_type",
                "",
            ),
        )

        row.setdefault(
            "start_type",
            race.get(
                "start_type",
                race.get(
                    "start",
                    "",
                ),
            ),
        )

        row.setdefault(
            "race_id",
            race.get(
                "race_id",
                "",
            ),
        )

        # Historical environment master stored descriptive
        # badge fields as scalar text. In live they can be lists.
        # They are NOT environment features, but make_race_row()
        # still carries them as audit/description fields.
        for descriptive_field in (
            "badges",
            "loppbadge",
            "loppbadge_x",
            "loppbadge_y",
        ):
            value = row.get(
                descriptive_field
            )

            if isinstance(
                value,
                (list, tuple, set),
            ):
                row[
                    descriptive_field
                ] = " | ".join(
                    str(item)
                    for item in value
                )

        rows.append(
            row
        )

    return pd.DataFrame(
        rows
    )


def _make_feature_row(
    race_data: dict,
    order: list[dict],
) -> dict:

    if not order:
        return {}

    race = race_data.get(
        "race",
        {},
    )

    date = _safe_int(
        race.get(
            "date",
            race.get(
                "race_date",
                0,
            ),
        ),
        0,
    )

    race_no = _safe_int(
        race.get(
            "race_no",
            0,
        ),
        0,
    )

    frame = _prepare_race_frame(
        race_data,
        order,
    )

    return make_race_row(
        date,
        race_no,
        frame,
    )


def _transform_feature_row(
    feature_row: dict,
    bundle: dict,
):

    frame = pd.DataFrame(
        [feature_row]
    )

    features = bundle[
        "features"
    ]

    # En kolumn kan saknas live om parametern
    # saknas helt i ett lopp.
    for feature in features:
        if feature not in frame.columns:
            frame[feature] = np.nan

    X = frame[
        features
    ].copy()

    for column in bundle[
        "numeric"
    ]:

        X[column] = pd.to_numeric(
            X[column],
            errors="coerce",
        )

        X[column] = (
            X[column]
            .fillna(
                bundle[
                    "medians"
                ][column]
            )
        )

    for column in bundle[
        "categorical"
    ]:

        X[column] = (
            X[column]
            .fillna(
                "Unknown"
            )
            .astype(str)
        )

    return X


def classify_environment(
    race_data: dict,
    order: list[dict],
    stage: str | None = None,
) -> dict:

    bundle = load_environment_model()

    if not order:
        result = {
            "environment": "UT",
            "leaf_id": None,
            "profile": None,
            "version": bundle.get(
                "version",
                "",
            ),
        }

        if stage:
            _store_result(
                race_data,
                order,
                stage,
                result,
            )

        return result

    feature_row = _make_feature_row(
        race_data,
        order,
    )

    X = _transform_feature_row(
        feature_row,
        bundle,
    )

    transformed = (
        bundle[
            "pipeline"
        ][
            "preprocessor"
        ].transform(X)
    )

    leaf_id = int(
        bundle[
            "pipeline"
        ][
            "tree"
        ].apply(
            transformed
        )[0]
    )

    leaf_map = {
        int(key): value
        for key, value
        in bundle[
            "leaf_to_environment"
        ].items()
    }

    environment = (
        leaf_map.get(
            leaf_id,
            "UT",
        )
    )

    profile = (
        bundle[
            "environment_profiles"
        ].get(
            environment
        )
    )

    result = {
        "environment":
            environment,

        "leaf_id":
            leaf_id,

        "profile":
            profile,

        "version":
            bundle.get(
                "version",
                "",
            ),

        "feature_row":
            feature_row,
    }

    if stage:
        _store_result(
            race_data,
            order,
            stage,
            result,
        )

    return result


def _store_result(
    race_data: dict,
    order: list[dict],
    stage: str,
    result: dict,
):

    race = race_data.setdefault(
        "race",
        {},
    )

    prefix = (
        f"{stage}_environment_v2"
    )

    race[prefix] = (
        result[
            "environment"
        ]
    )

    race[
        f"{stage}_environment_leaf_v2"
    ] = (
        result[
            "leaf_id"
        ]
    )

    race[
        f"{stage}_environment_profile_v2"
    ] = (
        result[
            "profile"
        ]
    )

    race[
        "environment_model_version_v2"
    ] = (
        result[
            "version"
        ]
    )

    for horse in order:

        horse[prefix] = (
            result[
                "environment"
            ]
        )

        horse[
            f"{stage}_environment_leaf_v2"
        ] = (
            result[
                "leaf_id"
            ]
        )

        horse[
            f"{stage}_environment_profile_v2"
        ] = (
            result[
                "profile"
            ]
        )


def environment_label(
    environment: str,
    profile: dict | None,
) -> str:

    icon = ENVIRONMENT_ICONS.get(
        environment,
        "⚫",
    )

    if (
        environment == "UT"
        or not profile
    ):
        return (
            f"{icon} Ingen låst miljö"
        )

    top3 = float(
        profile.get(
            "top3_pct",
            0,
        )
    )

    top5 = float(
        profile.get(
            "top5_pct",
            0,
        )
    )

    rank6 = float(
        profile.get(
            "rank6plus_pct",
            0,
        )
    )

    observations = int(
        profile.get(
            "observations",
            0,
        )
    )

    return (
        f"{icon} {environment} "
        f"| Top3 {top3:.1f}% "
        f"| Top5 {top5:.1f}% "
        f"| Rank6+ {rank6:.1f}% "
        f""
    )



