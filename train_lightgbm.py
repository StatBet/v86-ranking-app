import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score


DATASET_PATH = "ml_dataset.csv"


FEATURES = [
    "avg_odds",
    "form_score",
    "place_percent",
    "avg_time"
]


def evaluate_race_ranking(df, score_col):
    total_races = 0
    rank_1 = 0
    top_3 = 0
    top_5 = 0
    ranks = []

    for race_id, group in df.groupby("race_id"):
        if group["won"].sum() != 1:
            continue

        total_races += 1

        ranked = group.sort_values(
            score_col,
            ascending=False
        ).reset_index(drop=True)

        winner_index = ranked.index[ranked["won"] == 1][0]
        winner_rank = winner_index + 1

        ranks.append(winner_rank)

        if winner_rank == 1:
            rank_1 += 1

        if winner_rank <= 3:
            top_3 += 1

        if winner_rank <= 5:
            top_5 += 1

    return {
        "races": total_races,
        "rank_1": rank_1,
        "top_3": top_3,
        "top_5": top_5,
        "rank_1_pct": round(rank_1 / total_races * 100, 1),
        "top_3_pct": round(top_3 / total_races * 100, 1),
        "top_5_pct": round(top_5 / total_races * 100, 1),
        "avg_rank": round(sum(ranks) / len(ranks), 2)
    }


df = pd.read_csv(DATASET_PATH)

df = df.fillna(0)

df = df[df["race_id"].notna()]

df = df[df["won"].isin([0, 1])]

# Bara lopp där exakt en vinnare finns
valid_races = (
    df.groupby("race_id")["won"]
    .sum()
    .reset_index()
)

valid_races = valid_races[valid_races["won"] == 1]["race_id"]

df = df[df["race_id"].isin(valid_races)]

print("=" * 80)
print("DATASET")
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
    n_estimators=300,
    learning_rate=0.03,
    num_leaves=15,
    max_depth=4,
    min_child_samples=10,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42
)

model.fit(
    X_train,
    y_train
)

test_df["ml_score"] = model.predict_proba(X_test)[:, 1]

print()
print("=" * 80)
print("NUVARANDE MODELL PÅ TESTDATA")
print("=" * 80)
print(evaluate_race_ranking(test_df, "total_score"))

print()
print("=" * 80)
print("LIGHTGBM PÅ TESTDATA")
print("=" * 80)
print(evaluate_race_ranking(test_df, "ml_score"))

try:
    auc = roc_auc_score(y_test, test_df["ml_score"])
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