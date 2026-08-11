from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parent

DNA_COLUMNS = [
    "spike_score_race_rank",
    "speed_score_race_rank",
    "latest_start_score_race_rank",
    "driver_score_race_rank",
    "form_score_race_rank",
    "record_score_race_rank",
    "win_score_race_rank",
    "place_score_race_rank",
    "starts_score_race_rank",
]

RANKING_COLUMNS = [
    ("model_rank", True),
    ("rank_probability_percent", False),
    ("total_score", False),
    ("spike_score", False),
    ("speed_score", False),
    ("latest_start_score", False),
    ("form_score", False),
    ("driver_score", False),
    ("record_score", False),
    ("win_score", False),
    ("place_score", False),
    ("starts_score", False),
]

LEAF_GROUPS = {
    "Leaf 4": [4],
    "Leaf 5+10": [5, 10],
    "Leaf 8+19+20": [8, 19, 20],
}

# ============================================================
# SPÅR 1 - FRYSTA PREMIUMREGLER
# ============================================================

TRACK1_PREMIUM = {
    ("06", "Leaf 5+10"): (1000, 0.90),
    ("79", "Leaf 4"): (2250, 0.70),
    ("79", "Leaf 5+10"): (500, 0.85),
    ("79", "Leaf 8+19+20"): (500, 0.85),
}

TRACK1_FALLBACK1_DNA = 1750

# ============================================================
# SPÅR 2 - FRYSTA VARIANTREGLER
# ============================================================

TRACK2_RULES = [
    {
        "band": "06",
        "leaf_group": "Leaf 5+10",
        "variant": 1,
        "similarity": 0.85,
        "precision": 22.222222,
    },
    {
        "band": "79",
        "leaf_group": "Leaf 4",
        "variant": 1,
        "similarity": 0.85,
        "precision": 25.0,
    },
    {
        "band": "79",
        "leaf_group": "Leaf 4",
        "variant": 2,
        "similarity": 0.90,
        "precision": 37.5,
    },
    {
        "band": "79",
        "leaf_group": "Leaf 5+10",
        "variant": 1,
        "similarity": 0.95,
        "precision": 25.0,
    },
    {
        "band": "79",
        "leaf_group": "Leaf 8+19+20",
        "variant": 2,
        "similarity": 0.75,
        "precision": 20.0,
    },
]


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _leaf_group(leaf_id):
    leaf_id = _safe_int(leaf_id, -1)

    for name, values in LEAF_GROUPS.items():
        if leaf_id in values:
            return name

    return None


def _band(percent):
    p = _safe_float(percent, -1)

    if 0 <= p <= 6:
        return "06"

    if 7 <= p <= 9:
        return "79"

    return None


def _profile_filename(band, leaf_group):
    safe_leaf = (
        leaf_group
        .replace(" ", "_")
        .replace("+", "_")
    )

    return (
        BASE_DIR
        / f"winner_profiles_BUILD70_{band}_{safe_leaf}.csv"
    )


def _strength_filename(band):
    return BASE_DIR / f"strength_eval_{band}.csv"


# ============================================================
# FLATTEN LIVE OMGÅNG
# ============================================================

def _round_to_frame(processed_races):
    rows = []

    for race_index, race_data in enumerate(processed_races):
        race = race_data.get("race", {})
        horses = race_data.get("horses", [])

        race_no = race.get("race_no", race_index + 1)

        race_id = str(
            race.get(
                "race_id",
                f"LIVE_{race_no}",
            )
        )

        ranked_for_leaf = sorted(
            horses,
            key=lambda h: h.get("total_score", 0),
            reverse=True,
        )

        race_leaf_id = None

        if ranked_for_leaf:
            rank1 = ranked_for_leaf[0]

            race_leaf_id = rank1.get(
                "hybrid_environment_leaf_id",
                rank1.get(
                    "rank1_environment_leaf_id",
                    rank1.get("leaf_id"),
                ),
            )

        for horse_index, horse in enumerate(horses):
            horse["_skrall_live_index"] = (
                race_index,
                horse_index,
            )

            row = dict(horse)

            row["race_id"] = race_id
            row["race_no"] = race_no
            row["leaf_id"] = race_leaf_id

            row["horse"] = horse.get(
                "horse",
                horse.get("name", ""),
            )

            row["number"] = horse.get(
                "number",
                horse.get("post", ""),
            )

            rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# RANKING INOM VARJE LOPP
# ============================================================

def _add_within_race_ranks(df):
    work = df.copy()

    for column, ascending in RANKING_COLUMNS:
        if column not in work.columns:
            continue

        values = pd.to_numeric(
            work[column],
            errors="coerce",
        )

        work[column] = values

        work[f"{column}_race_rank"] = (
            work
            .groupby("race_id")[column]
            .rank(
                method="min",
                ascending=ascending,
            )
        )

    return work


# ============================================================
# STRENGTH-DNA / DNA_SCORE
# ============================================================

def _build_candidate_scores(df, band):
    strength_file = _strength_filename(band)

    if not strength_file.exists():
        raise FileNotFoundError(
            f"Saknar {strength_file.name}"
        )

    strength = pd.read_csv(strength_file)

    if band == "06":
        work = df[
            pd.to_numeric(
                df["percent"],
                errors="coerce",
            ).between(0, 6)
        ].copy()

    else:
        work = df[
            pd.to_numeric(
                df["percent"],
                errors="coerce",
            ).between(7, 9)
        ].copy()

    matches = []

    for _, rule_row in strength.iterrows():
        group_name = rule_row["leaf_group"]

        leafs = LEAF_GROUPS.get(
            group_name,
            [],
        )

        group = work[
            work["leaf_id"]
            .apply(_safe_int)
            .isin(leafs)
        ].copy()

        if group.empty:
            continue

        signature_text = str(
            rule_row["signature"]
        )

        rules = [
            x.strip()
            for x in signature_text.split("+")
        ]

        mask = pd.Series(
            True,
            index=group.index,
        )

        valid = True

        for rule in rules:
            if "<=Top" not in rule:
                valid = False
                break

            column, limit_text = rule.split(
                "<=Top",
                1,
            )

            column = column.strip()
            limit = _safe_int(
                limit_text.strip(),
                999,
            )

            if column not in group.columns:
                valid = False
                break

            values = pd.to_numeric(
                group[column],
                errors="coerce",
            )

            mask &= values <= limit

        if not valid:
            continue

        selected = group[mask]

        if selected.empty:
            continue

        parameters = _safe_int(
            rule_row.get(
                "parameters",
                len(rules),
            )
        )

        coverage = _safe_float(
            rule_row.get(
                "skrallwinner_coverage",
                0,
            )
        )

        points = coverage * parameters

        for idx in selected.index:
            matches.append({
                "_row_index": idx,
                "signature": signature_text,
                "match_points": points,
                "coverage": coverage,
                "parameters": parameters,
            })

    if not matches:
        return pd.DataFrame()

    m = pd.DataFrame(matches)

    agg = (
        m.groupby(
            "_row_index",
            as_index=False,
        )
        .agg(
            dna_matches=(
                "signature",
                "nunique",
            ),
            dna_score=(
                "match_points",
                "sum",
            ),
            best_rule_coverage=(
                "coverage",
                "max",
            ),
            max_parameters=(
                "parameters",
                "max",
            ),
        )
    )

    result = (
        df.reset_index()
        .rename(columns={"index": "_row_index"})
        .merge(
            agg,
            on="_row_index",
            how="inner",
        )
    )

    result["band"] = band
    result["leaf_group"] = result[
        "leaf_id"
    ].apply(_leaf_group)

    return result


# ============================================================
# DNA-PROFIL + KMEANS-LIKHET
# ============================================================

def _load_cluster_model(band, leaf_group):
    profile_file = _profile_filename(
        band,
        leaf_group,
    )

    if not profile_file.exists():
        raise FileNotFoundError(
            f"Saknar {profile_file.name}"
        )

    winners = pd.read_csv(profile_file)

    features = [
        c
        for c in winners.columns
        if c not in [
            "date",
            "race_id",
            "horse",
        ]
    ]

    model = KMeans(
        n_clusters=3,
        random_state=42,
        n_init=100,
    )

    model.fit(
        winners[features].fillna(0)
    )

    return model, features


def _candidate_profile_from_strengths(
    row_index,
    band_scores,
    band,
    leaf_group,
):
    strength_file = _strength_filename(band)
    strength = pd.read_csv(strength_file)

    strength = strength[
        strength["leaf_group"] == leaf_group
    ]

    if strength.empty:
        return None

    source_row = band_scores.loc[
        band_scores["_row_index"] == row_index
    ]

    if source_row.empty:
        return None

    source_row = source_row.iloc[0]

    counts = {
        c: 0
        for c in DNA_COLUMNS
    }

    for _, rule_row in strength.iterrows():
        signature = str(rule_row["signature"])

        rules = [
            x.strip()
            for x in signature.split("+")
        ]

        matches = True
        used = []

        for rule in rules:
            if "<=Top" not in rule:
                matches = False
                break

            column, limit_text = rule.split(
                "<=Top",
                1,
            )

            column = column.strip()
            limit = _safe_int(
                limit_text.strip(),
                999,
            )

            value = _safe_float(
                source_row.get(
                    column,
                    999,
                ),
                999,
            )

            if value > limit:
                matches = False
                break

            used.append(column)

        if matches:
            for column in used:
                if column in counts:
                    counts[column] += 1

    total = sum(counts.values())

    if total == 0:
        return None

    return counts


def _add_variant_similarity(scores, band):
    if scores.empty:
        return scores.copy()

    output = []

    for leaf_group in LEAF_GROUPS:
        group = scores[
            scores["leaf_group"]
            == leaf_group
        ].copy()

        if group.empty:
            continue

        model, features = _load_cluster_model(
            band,
            leaf_group,
        )

        for _, row in group.iterrows():
            counts = _candidate_profile_from_strengths(
                row["_row_index"],
                scores,
                band,
                leaf_group,
            )

            if not counts:
                continue

            # Winner-profilefilerna består av
            # normaliserade styrkeprofiler.
            total = sum(counts.values())

            vector_values = []

            for feature in features:
                if feature in counts:
                    vector_values.append(
                        counts[feature] / total
                    )
                else:
                    vector_values.append(0)

            profile = np.array(
                vector_values,
                dtype=float,
            ).reshape(1, -1)

            sims = cosine_similarity(
                profile,
                model.cluster_centers_,
            )[0]

            item = row.to_dict()

            item["dna_variant"] = (
                int(np.argmax(sims)) + 1
            )

            item["variant_similarity"] = float(
                np.max(sims)
            )

            output.append(item)

    return pd.DataFrame(output)


# ============================================================
# SPÅR 1
# ============================================================

def _select_track1(scores06, scores79):
    all_scores = pd.concat(
        [scores06, scores79],
        ignore_index=True,
    )

    sim06 = _add_variant_similarity(
        scores06,
        "06",
    )

    sim79 = _add_variant_similarity(
        scores79,
        "79",
    )

    sim = pd.concat(
        [sim06, sim79],
        ignore_index=True,
    )

    premium_parts = []

    for (
        band,
        leaf_group
    ), (
        dna_limit,
        sim_limit
    ) in TRACK1_PREMIUM.items():

        x = sim[
            (sim["band"] == band)
            &
            (
                sim["leaf_group"]
                == leaf_group
            )
            &
            (
                sim["dna_score"]
                >= dna_limit
            )
            &
            (
                sim["variant_similarity"]
                >= sim_limit
            )
        ].copy()

        if x.empty:
            continue

        x["_track1_priority"] = (
            x["dna_score"]
            / dna_limit
            * x["variant_similarity"]
        )

        premium_parts.append(x)

    if premium_parts:
        premium = pd.concat(
            premium_parts,
            ignore_index=True,
        )

        premium = (
            premium
            .sort_values(
                [
                    "_track1_priority",
                    "dna_score",
                ],
                ascending=False,
            )
            .drop_duplicates(
                "_row_index"
            )
            .sort_values(
                "_track1_priority",
                ascending=False,
            )
            .head(4)
        )
    else:
        premium = pd.DataFrame()

    selected = set(
        premium["_row_index"]
        if not premium.empty
        else []
    )

    # Premium finns -> Spår 1 stannar där.
    if selected:
        return selected

    # FALLBACK 1
    fallback1 = all_scores[
        all_scores["dna_score"]
        >= TRACK1_FALLBACK1_DNA
    ].copy()

    if not fallback1.empty:
        best = (
            fallback1
            .sort_values(
                [
                    "dna_score",
                    "best_rule_coverage",
                ],
                ascending=False,
            )
            .head(1)
        )

        return set(best["_row_index"])

    # FALLBACK 2
    if sim.empty:
        return set()

    best = (
        sim
        .sort_values(
            [
                "variant_similarity",
                "dna_score",
            ],
            ascending=False,
        )
        .head(1)
    )

    return set(best["_row_index"])


# ============================================================
# SPÅR 2
# ============================================================

def _select_track2(scores06, scores79):
    sim = pd.concat(
        [
            _add_variant_similarity(
                scores06,
                "06",
            ),
            _add_variant_similarity(
                scores79,
                "79",
            ),
        ],
        ignore_index=True,
    )

    if sim.empty:
        return set()

    parts = []

    for rule in TRACK2_RULES:
        x = sim[
            (sim["band"] == rule["band"])
            &
            (
                sim["leaf_group"]
                == rule["leaf_group"]
            )
            &
            (
                sim["dna_variant"]
                == rule["variant"]
            )
            &
            (
                sim["variant_similarity"]
                >= rule["similarity"]
            )
        ].copy()

        if x.empty:
            continue

        x["_track2_rule_precision"] = (
            rule["precision"]
        )

        parts.append(x)

    if not parts:
        return set()

    pool = pd.concat(
        parts,
        ignore_index=True,
    )

    pool = (
        pool
        .sort_values(
            [
                "_track2_rule_precision",
                "variant_similarity",
                "dna_score",
            ],
            ascending=False,
        )
        .drop_duplicates(
            "_row_index"
        )
        .head(2)
    )

    return set(pool["_row_index"])


# ============================================================
# PUBLIK FUNKTION
# ============================================================

def apply_skrall_badges(processed_races):
    """
    Applicerar de två frysta skrällbadgesen över en hel omgång.

    SKRÄLL PREMIUM:
        vald av både Spår 1 och Spår 2

    SKRÄLLKANDIDAT:
        vald av exakt ett av spåren
    """

    df = _round_to_frame(processed_races)

    if df.empty:
        return processed_races

    df = _add_within_race_ranks(df)

    scores06 = _build_candidate_scores(
        df,
        "06",
    )

    scores79 = _build_candidate_scores(
        df,
        "79",
    )

    track1 = _select_track1(
        scores06,
        scores79,
    )

    track2 = _select_track2(
        scores06,
        scores79,
    )

    selected = track1 | track2

    for idx, row in df.iterrows():
        live_index = row.get(
            "_skrall_live_index"
        )

        if not isinstance(
            live_index,
            tuple,
        ):
            continue

        race_index, horse_index = live_index

        horse = processed_races[
            race_index
        ]["horses"][horse_index]

        badges = horse.get("badges", [])

        if badges is None:
            badges = []
        elif isinstance(badges, str):
            badges = [badges] if badges.strip() else []
        else:
            badges = list(badges)

        horse["badges"] = badges

        # Säkerställ att gamla skrällbadges inte ligger kvar
        badges[:] = [
            b
            for b in badges
            if b not in {
                "⭐ SKRÄLL PREMIUM",
                "💥 SKRÄLLKANDIDAT",
            }
        ]

        if idx not in selected:
            horse["skrall_track1"] = False
            horse["skrall_track2"] = False
            horse["skrall_premium"] = False
            horse["skrall_candidate"] = False
            continue

        hit1 = idx in track1
        hit2 = idx in track2

        horse["skrall_track1"] = hit1
        horse["skrall_track2"] = hit2
        horse["skrall_premium"] = (
            hit1 and hit2
        )
        horse["skrall_candidate"] = True

        if hit1 and hit2:
            badges.append(
                "⭐ SKRÄLL PREMIUM"
            )
        else:
            badges.append(
                "💥 SKRÄLLKANDIDAT"
            )

    return processed_races