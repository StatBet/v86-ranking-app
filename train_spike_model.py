import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score


DATASET_PATH = "spike_dataset.csv"


FEATURES = [
    "total_score",
    "score_gap",
    "win_percent",
    "place_percent",
    "form_score",
    "latest_start_score",
    "driver_score",
    "post_score",
    "avg_time",
    "avg_odds",
    "class_change_score",
    "gallop_score",
    "post",
    "field_size",
    "is_post_1_6",
    "is_post_7_8",
    "is_post_9_plus",
    "is_field_10_or_less",
    "is_field_11_12",
    "is_field_13_plus",
    "gap_10_plus",
    "gap_20_plus",
    "gap_30_plus",
    "good_spike_zone",
    "bad_spike_zone",
]


def evaluate_by_date(df, score_col):
    rows = []

    for picks_per_date in [2, 3, 4]:
        selected = []

        for date, group in df.groupby("date"):
            picks = group.sort_values(
                score_col,
                ascending=False
            ).head(picks_per_date)

            selected.append(picks)

        selected_df = pd.concat(selected)

        total = len(selected_df)
        wins = int(selected_df["won"].sum())
        pct = round(wins / total * 100, 1)

        rows.append({
            "spikar_per_omgang": picks_per_date,
            "spikar": total,
            "ratt": wins,
            "traff_pct": pct
        })

    return pd.DataFrame(rows)


df = pd.read_csv(DATASET_PATH)
df = df.fillna(0)

print("=" * 80)
print("SPIKE MODEL DATASET")
print("=" * 80)
print("Rader:", len(df))
print("Rätt:", int(df["won"].sum()))
print("Basträff:", round(df["won"].mean() * 100, 1))

X = df[FEATURES]
y = df["won"]
groups = df["date"]

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.25,
    random_state=42
)

train_idx, test_idx = next(
    splitter.split(X, y, groups)
)

train_df = df.iloc[train_idx].copy()
test_df = df.iloc[test_idx].copy()

X_train = train_df[FEATURES]
y_train = train_df["won"]

X_test = test_df[FEATURES]
y_test = test_df["won"]

model = lgb.LGBMClassifier(
    objective="binary",
    n_estimators=250,
    learning_rate=0.03,
    num_leaves=7,
    max_depth=3,
    min_child_samples=10,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42
)

model.fit(X_train, y_train)

test_df["ml_spike_score"] = model.predict_proba(X_test)[:, 1]

print()
print("=" * 80)
print("ML SPIKMODELL")
print("=" * 80)
print(evaluate_by_date(test_df, "ml_spike_score").to_string(index=False))

print()
print("=" * 80)
print("NUVARANDE SPIKE SCORE")
print("=" * 80)
print(evaluate_by_date(test_df, "total_score").to_string(index=False))

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