import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[df["model_rank"].between(6,8)].copy()

rank68["badge_points"] = 0
rank68["badge_points"] += (rank68["win_percent"] >= 20).astype(int)
rank68["badge_points"] += (rank68["place_percent"] >= 45).astype(int)
rank68["badge_points"] += (rank68["form_score"] >= 20).astype(int)
rank68["badge_points"] += (rank68["latest_start_score"] >= 5).astype(int)
rank68["badge_points"] += (rank68["avg_odds"] <= 15).astype(int)

badge = rank68[rank68["badge_points"] >= 4].copy()

rank68["spike_score"] = (
    rank68["win_percent"] * 2
    + rank68["form_score"] * 1.5
    + rank68["place_percent"]
)

spike = rank68[
    rank68["spike_score"] >= 120
].copy()

badge_set = set(
    badge["date"].astype(str)
    + "_"
    + badge["race_no"].astype(str)
    + "_"
    + badge["horse"]
)

spike_set = set(
    spike["date"].astype(str)
    + "_"
    + spike["race_no"].astype(str)
    + "_"
    + spike["horse"]
)

both = badge_set & spike_set

print("=" * 80)
print("BADGE VS SPIKE")
print("=" * 80)

print()
print("Badge:", len(badge_set))
print("Spike:", len(spike_set))
print("Båda:", len(both))

print()
print("Badge endast:", len(badge_set - spike_set))
print("Spike endast:", len(spike_set - badge_set))