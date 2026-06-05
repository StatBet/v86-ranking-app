import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score


DATASET_PATH = "ml_dataset.csv"


FEATURES = [
    "total_score",
    "avg_odds",
    "form_score",
    "place_percent",
    "win_percent",
    "avg_time",
    "post",
    "field_size",
    "gallop_score",
    "driver_score",
    "class_change_score",
    "percent",
]


def evaluate_spikes(df, score_col):
    rows = []

    for picks_per_date in [2, 3, 4]:
        selected = []

        for date, group in df.groupby("date"):
            rank1 = group[group["is_model_rank_1"] == 1].copy()

            if rank1.empty:
                continue

            picks = rank1.sort_values(
                score_col,
                ascending=False
            ).head(picks_per_date)

            selected.append(picks)

        selected_df = pd.concat(selected) if selected else pd.DataFrame()

        total = len(selected_df)
        wins = int(selected_df["won"].sum()) if total else 0
        pct = round(wins / total * 100, 1) if total else 0

        rows.append({
            "spikar_per_omgang": picks_per_date,
            "spikar": total,
            "ratt": wins,
            "traff_pct": pct
        })

    return pd.DataFrame(rows)


df = pd.read_csv(DATASET_PATH)
df = df.fillna(0)

df = df[df["race_id"].notna()]
df = df[df["won"].isin([0, 1])]

valid_races = (
    df.groupby("race_id")["won"]
    .sum()
    .reset_index()
)

valid_races = valid_races[valid_races["won"] == 1]["race_id"]
df = df[df["race_id"].isin(valid_races)].copy()

df["back_post_large_field"] = (
    (
        (df["start_type"] == "auto") &
        (df["post"].between(9, 12)) &
        (df["field_size"] >= 12)
    )
    |
    (
        (df["start_type"] == "volt") &
        (df["post"].between(8, 15)) &
        (df["field_size"] >= 12)
    )
).astype(int)

FEATURES.append("back_post_large_field")

print("=" * 80)
print("LIGHTGBM SPIKMODELL")
print("=" * 80)
print("Rader:", len(df))
print("Lopp:", df["race_id"].nunique())
print("Vinnare:", int(df["won"].sum()))

X = df[FEATURES]
y = df["won"]
groups = df["race_id"]

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.25,
    random_state=42
)

train_idx, test_idx = next(splitter.split(X, y, groups))

train_df = df.iloc[train_idx].copy()
test_df = df.iloc[test_idx].copy()

X_train = train_df[FEATURES]
y_train = train_df["won"]

X_test = test_df[FEATURES]
y_test = test_df["won"]

model = lgb.LGBMClassifier(
    objective="binary",
    n_estimators=300,
    learning_rate=0.03,
    num_leaves=15,
    max_depth=4,
    min_child_samples=15,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42
)

model.fit(X_train, y_train)

test_df["ml_spike_score"] = model.predict_proba(X_test)[:, 1]

print()
print("=" * 80)
print("SPIKTEST - LIGHTGBM")
print("=" * 80)
print(evaluate_spikes(test_df, "ml_spike_score").to_string(index=False))

print()
print("=" * 80)
print("SPIKTEST - TOTAL_SCORE")
print("=" * 80)
print(evaluate_spikes(test_df, "total_score").to_string(index=False))

try:
    auc = roc_auc_score(y_test, test_df["ml_spike_score"])
    print()
    print("AUC:", round(auc, 3))
except Exception:
    pass

print()
print("=" * 80)
print("FEATURE IMPORTANCE")
print("=" * 80)

importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": model.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

print(importance.to_string(index=False))