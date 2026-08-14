from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import copy

import joblib
import numpy as np
import pandas as pd

try:
    from skrall_v2.BUILD_ENVIRONMENT_MASTER import make_race_row
except ModuleNotFoundError:
    from BUILD_ENVIRONMENT_MASTER import make_race_row


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
        f"| BUILD n={observations}"
    )

