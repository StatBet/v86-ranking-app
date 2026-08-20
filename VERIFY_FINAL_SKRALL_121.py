from pathlib import Path
import pandas as pd

import v8x_postprocess as v8x
from environment_live_engine import classify_environment
from BASELINE_CURRENT_SKRALL_BUILD90 import build_round

from live_hybrid_spike_engine_BEFORE_D_20260818 import (
    get_hybrid_round_spikes as get_legacy_hybrid_round_spikes,
)

from badge_engine import (
    calculate_spike_score,
    _rank_horses_by_total_score,
    apply_system_only_value_flags,
)

from skrall_badge_engine import apply_skrall_badges

ROOT = Path(__file__).resolve().parent
HIST = ROOT / "historical_rankings.csv"



EXPECTED = {
    "rounds": 121,
    "06_candidates": 91,
    "06_winners": 16,
    "79_candidates": 55,
    "79_winners": 12,
    "main_candidates": 146,
    "main_winners": 28,
    "fallback_candidates": 53,
    "fallback_winners": 13,
    "total_candidates": 199,
    "total_winners": 41,
}

def as_int(value, default=0):
    try:
        if value is None or pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


if not HIST.exists():
    raise SystemExit(f"STOPP: saknar {HIST}")

df = pd.read_csv(HIST, low_memory=False)

required = {
    "date",
    "race_id",
    "horse",
    "won",
    "percent",
    "total_score",
    "spike_score",
    "post_score",
    "prize_money_score",
}
missing = sorted(required - set(df.columns))

if missing:
    raise SystemExit(
        "STOPP: historical_rankings.csv saknar: "
        + ", ".join(missing)
    )

df["date"] = pd.to_numeric(
    df["date"],
    errors="coerce",
).astype("Int64")

dates = sorted(
    int(x)
    for x in df["date"].dropna().unique()
)

print("=" * 100)
print("FINAL SKRÄLL 121 — PRODUKTIONSREGRESSION")
print("=" * 100)
print("Historical:", HIST)
print("Omgångar:", len(dates))
print("Datum:", dates[0], "-", dates[-1])
print()

if len(dates) != EXPECTED["rounds"]:
    raise SystemExit(
        f"STOPP: fick {len(dates)} omgångar, "
        f"förväntat {EXPECTED['rounds']}."
    )

rows = []

for date in dates:
    round_df = df[df["date"] == date].copy()
    processed_races = build_round(round_df)

    # ========================================================
    # 1. INITIAL ENVIRONMENT V2
    # ========================================================
    for race_data in processed_races:
        initial_order = sorted(
            race_data.get("horses", []),
            key=lambda h: float(
                h.get("total_score", 0) or 0
            ),
            reverse=True,
        )

        classify_environment(
            race_data,
            initial_order,
            stage="initial",
        )

    # ========================================================
    # 2. LEGACY HYBRID
    #
    # EXAKT SOM LIVE-APPEN:
    # skapar de gamla leaf/environment-fälten som frysta
    # Skräll/V8X/79 fortfarande använder.
    # ========================================================
    legacy_top_spikes = get_legacy_hybrid_round_spikes(
        all_races=processed_races,
        calculate_spike_score=calculate_spike_score,
        rank_horses=_rank_horses_by_total_score,
        apply_value_flags=apply_system_only_value_flags,
    )

    # ========================================================
    # 3. FRYST SKRÄLLMOTOR
    #
    # Behövs för samma legacy leaf/environment-data som live.
    # V8X rensar därefter gamla slutval och äger final 06/79.
    # ========================================================
    processed_races = apply_skrall_badges(
        processed_races
    )

    # ========================================================
    # 4. V8X FINAL RANKING + 06-A CLEAN / gamla 79
    # ========================================================
    processed_races = v8x.apply_v8x_postprocess(
        processed_races
    )

    # Spara huvudgruppen innan fallback.
    for race_data in processed_races:
        race = race_data.get("race", {})

        for h in race_data.get("horses", []):
            variant = str(
                h.get("skrall_variant", "")
            ).strip()

            if (
                h.get("skrall_selected", False)
                and variant in {"06", "79"}
            ):
                rows.append({
                    "date": date,
                    "race_id": race.get("race_id", ""),
                    "race_no": race.get("race_no", ""),
                    "horse": h.get("horse", ""),
                    "variant": variant,
                    "won": as_int(h.get("won"), 0),
                    "percent": h.get("percent", 0),
                    "phase": "MAIN",
                })

    # ========================================================
    # 3. FINAL ENVIRONMENT V2
    # ========================================================
    for race_data in processed_races:
        final_order = sorted(
            race_data.get("horses", []),
            key=lambda h: h.get(
                "_final_rank",
                h.get("final_rank", 999),
            ),
        )

        classify_environment(
            race_data,
            final_order,
            stage="final",
        )

    # ========================================================
    # 4. BRED-ENV A + DIRECT-B FALLBACK
    # ========================================================
    processed_races = (
        v8x.apply_final_skrall_fallback(
            processed_races
        )
    )

    # Bara fallback-picks.
    for race_data in processed_races:
        race = race_data.get("race", {})

        for h in race_data.get("horses", []):
            variant = str(
                h.get("skrall_variant", "")
            ).strip()

            if variant not in {
                "BRED-ENV A",
                "DIRECT-B",
                "BRED-ENV A + DIRECT-B",
            }:
                continue

            if not h.get("skrall_selected", False):
                continue

            rows.append({
                "date": date,
                "race_id": race.get("race_id", ""),
                "race_no": race.get("race_no", ""),
                "horse": h.get("horse", ""),
                "variant": variant,
                "won": as_int(h.get("won"), 0),
                "percent": h.get("percent", 0),
                "phase": "FALLBACK",
            })


out = pd.DataFrame(rows)

if out.empty:
    raise SystemExit("STOPP: verifieringen gav 0 kandidater.")

# Säkerhetskontroll: samma häst/race får bara räknas en gång.
dupes = out.duplicated(
    ["date", "race_id", "horse"],
    keep=False,
)

if dupes.any():
    print()
    print("STOPP: DUBBLA KANDIDATER")
    print(
        out.loc[
            dupes,
            [
                "date",
                "race_id",
                "horse",
                "variant",
                "phase",
            ],
        ].to_string(index=False)
    )
    raise SystemExit(1)


six = out[out["variant"] == "06"]
sevennine = out[out["variant"] == "79"]
main = out[out["phase"] == "MAIN"]
fallback = out[out["phase"] == "FALLBACK"]

actual = {
    "rounds": len(dates),
    "06_candidates": len(six),
    "06_winners": int(six["won"].sum()),
    "79_candidates": len(sevennine),
    "79_winners": int(sevennine["won"].sum()),
    "main_candidates": len(main),
    "main_winners": int(main["won"].sum()),
    "fallback_candidates": len(fallback),
    "fallback_winners": int(fallback["won"].sum()),
    "total_candidates": len(out),
    "total_winners": int(out["won"].sum()),
}

print("=" * 100)
print("RESULTAT")
print("=" * 100)

print(
    f"06-A CLEAN       "
    f"{actual['06_candidates']} / "
    f"{actual['06_winners']}"
)

print(
    f"Gamla 79         "
    f"{actual['79_candidates']} / "
    f"{actual['79_winners']}"
)

print(
    f"06 + 79          "
    f"{actual['main_candidates']} / "
    f"{actual['main_winners']}"
)

print(
    f"A+B fallback     "
    f"{actual['fallback_candidates']} / "
    f"{actual['fallback_winners']}"
)

print(
    f"TOTALT           "
    f"{actual['total_candidates']} / "
    f"{actual['total_winners']}"
)

print()

fallback_breakdown = (
    fallback.groupby("variant")["won"]
    .agg(["count", "sum"])
)

print("FALLBACK PER VARIANT")
print(fallback_breakdown.to_string())
print()


failed = []

for key, expected in EXPECTED.items():
    got = actual[key]

    status = "OK" if got == expected else "FEL"

    print(
        f"{status:3}  "
        f"{key:20} "
        f"got={got:<4} "
        f"expected={expected}"
    )

    if got != expected:
        failed.append(
            (key, got, expected)
        )


out.to_csv(
    ROOT / "VERIFY_FINAL_SKRALL_121_candidates.csv",
    index=False,
    encoding="utf-8-sig",
)

winners = out[out["won"] == 1].copy()

winners.to_csv(
    ROOT / "VERIFY_FINAL_SKRALL_121_winners.csv",
    index=False,
    encoding="utf-8-sig",
)


print()
print("=" * 100)

if failed:
    print("❌ REGRESSION FAILED")
    print("=" * 100)

    print()
    print("Avvikelser:")

    for key, got, expected in failed:
        print(
            f" - {key}: "
            f"{got} istället för {expected}"
        )

    print()
    print("INGEN GIT PUSH FÅR GÖRAS.")
    raise SystemExit(1)

print("✅ ALLA KONTROLLSUMMOR STÄMMER")
print("✅ 121 / 199 kandidater / 41 vinnare")
print("=" * 100)

print()
print("VINNARNA:")
print(
    winners[
        [
            "date",
            "race_no",
            "horse",
            "variant",
        ]
    ]
    .sort_values(
        ["date", "race_no", "horse"]
    )
    .to_string(index=False)
)
