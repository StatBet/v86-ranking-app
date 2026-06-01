import streamlit as st
import pandas as pd
import docx
from datetime import datetime

from scripts.ranking_engine_v3 import (
    parse_input,
    add_dynamic_scores,
    calculate_total_score,
    scoring_rules
)

from scripts.parser_atg_new import parse_new_atg_format


st.set_page_config(page_title="V86 Ranking App", layout="wide")
st.title("V86 Ranking App")


def read_docx(file):
    doc = docx.Document(file)
    text = []

    for para in doc.paragraphs:
        if para.text.strip():
            text.append(para.text.strip())

    for table in doc.tables:
        for row in table.rows:
            cells = []
            for cell in row.cells:
                if cell.text.strip():
                    cells.append(cell.text.strip())
            if cells:
                text.append(" | ".join(cells))

    return "\n".join(text)


def clean_atg_header(raw_data):
    if "Avdelning 1," in raw_data:
        raw_data = raw_data.split("Avdelning 1,", 1)[1]
        raw_data = "Avdelning 1," + raw_data
    elif "Avdelning 1" in raw_data:
        raw_data = raw_data.split("Avdelning 1", 1)[1]
        raw_data = "Avdelning 1" + raw_data

    return raw_data


def int_slider(label, value, min_value=-50, max_value=50, key=None):
    return st.slider(
        label,
        min_value=min_value,
        max_value=max_value,
        value=int(value),
        step=1,
        key=key
    )


st.sidebar.title("Poängpanel")
st.sidebar.caption("Ändra poäng här. Resultatet uppdateras automatiskt.")


with st.sidebar.expander("Spel%", expanded=True):
    use_spel_percent = st.toggle(
        "Använd spel% i totalpoäng",
        value=False,
        key="sidebar_use_spel_percent"
    )

    for i, value in enumerate(scoring_rules["spel_percent_points"]):
        scoring_rules["spel_percent_points"][i] = int_slider(
            f"Spel% grupp {i + 1}",
            value,
            0,
            40,
            f"sidebar_spel_{i}"
        )

    scoring_rules["spel_percent_group_threshold"] = int_slider(
        "Gruppgräns %-enheter",
        scoring_rules["spel_percent_group_threshold"],
        0,
        10,
        "sidebar_spel_threshold"
    )


with st.sidebar.expander("Snittodds"):
    for i, row in enumerate(scoring_rules["avg_odds_ranges"]):
        row["points"] = int_slider(
            f"Odds {row['min']}–{row['max']}",
            row["points"],
            0,
            40,
            f"sidebar_odds_{i}"
        )


with st.sidebar.expander("Seger%"):
    for i, value in enumerate(scoring_rules["win_percent_points"]):
        scoring_rules["win_percent_points"][i] = int_slider(
            f"Seger% grupp {i + 1}",
            value,
            0,
            40,
            f"sidebar_win_{i}"
        )

    scoring_rules["win_percent_group_threshold"] = int_slider(
        "Gruppgräns %-enheter",
        scoring_rules["win_percent_group_threshold"],
        0,
        10,
        "sidebar_win_threshold"
    )


with st.sidebar.expander("Plats%"):
    for i, value in enumerate(scoring_rules["place_percent_points"]):
        scoring_rules["place_percent_points"][i] = int_slider(
            f"Plats% grupp {i + 1}",
            value,
            0,
            40,
            f"sidebar_place_{i}"
        )

    scoring_rules["place_percent_group_threshold"] = int_slider(
        "Gruppgräns %-enheter",
        scoring_rules["place_percent_group_threshold"],
        0,
        10,
        "sidebar_place_threshold"
    )


with st.sidebar.expander("Prissumma"):
    for i, value in enumerate(scoring_rules["prize_money_points"]):
        scoring_rules["prize_money_points"][i] = int_slider(
            f"Prissumma grupp {i + 1}",
            value,
            0,
            40,
            f"sidebar_prize_{i}"
        )

    scoring_rules["prize_money_group_threshold_percent"] = int_slider(
        "Gruppgräns %",
        scoring_rules["prize_money_group_threshold_percent"],
        0,
        20,
        "sidebar_prize_threshold"
    )


with st.sidebar.expander("Senaste 5 prispengar"):
    for i, row in enumerate(scoring_rules.get("recent_prize_ranges", [])):
        row["points"] = int_slider(
            f"Min {row['min']} kr",
            row["points"],
            0,
            30,
            f"sidebar_recent_prize_{i}"
        )


with st.sidebar.expander("Kuskmodell"):
    st.caption("Automatisk kuskpoäng hämtas från config/driver_stats.json.")

    scoring_rules["driver_min_starts"] = int_slider(
        "Minsta antal lopp för kuskpoäng",
        scoring_rules.get("driver_min_starts", 70),
        0,
        500,
        "sidebar_driver_min_starts"
    )

    scoring_rules["driver_mid_starts"] = int_slider(
        "Gräns nivå 2",
        scoring_rules.get("driver_mid_starts", 150),
        0,
        1000,
        "sidebar_driver_mid_starts"
    )

    scoring_rules["driver_high_starts"] = int_slider(
        "Gräns nivå 3",
        scoring_rules.get("driver_high_starts", 300),
        0,
        1500,
        "sidebar_driver_high_starts"
    )

    scoring_rules["driver_low_multiplier"] = st.slider(
        "Multiplier låg nivå",
        min_value=0.0,
        max_value=2.0,
        value=float(scoring_rules.get("driver_low_multiplier", 0.75)),
        step=0.05,
        key="sidebar_driver_low_multiplier"
    )

    scoring_rules["driver_mid_multiplier"] = st.slider(
        "Multiplier mellan nivå",
        min_value=0.0,
        max_value=2.0,
        value=float(scoring_rules.get("driver_mid_multiplier", 1.0)),
        step=0.05,
        key="sidebar_driver_mid_multiplier"
    )

    scoring_rules["driver_high_multiplier"] = st.slider(
        "Multiplier hög nivå",
        min_value=0.0,
        max_value=2.0,
        value=float(scoring_rules.get("driver_high_multiplier", 1.25)),
        step=0.05,
        key="sidebar_driver_high_multiplier"
    )


with st.sidebar.expander("Form"):
    for placement in list(scoring_rules["form_points"].keys()):
        scoring_rules["form_points"][placement] = int_slider(
            f"Placering {placement}",
            scoring_rules["form_points"][placement],
            0,
            25,
            f"sidebar_form_{placement}"
        )


with st.sidebar.expander("Senaste start"):
    for placement in list(scoring_rules["latest_start_points"].keys()):
        scoring_rules["latest_start_points"][placement] = int_slider(
            f"Senaste start {placement}",
            scoring_rules["latest_start_points"][placement],
            0,
            25,
            f"sidebar_latest_{placement}"
        )


with st.sidebar.expander("Starter"):
    for i, row in enumerate(scoring_rules["starts_points"]):
        row["points"] = int_slider(
            f"{row['min']}–{row['max']} starter",
            row["points"],
            -30,
            30,
            f"sidebar_starts_{i}"
        )


with st.sidebar.expander("Rekord"):
    st.caption("Rekordpoängen beräknas nu relativt inom loppet.")


with st.sidebar.expander("Vagn / Skor / Manuell"):
    scoring_rules["american_wagon_bonus"] = int_slider(
        "Amerikansk vagn bonus",
        scoring_rules["american_wagon_bonus"],
        0,
        30,
        "sidebar_wagon_bonus"
    )

    scoring_rules["american_wagon_max_recent_count"] = int_slider(
        "Max amerikansk senaste 5",
        scoring_rules["american_wagon_max_recent_count"],
        0,
        5,
        "sidebar_wagon_recent"
    )

    manual_shoe_bonus = int_slider(
        "Skorpoäng per ikryssad häst",
        0,
        -20,
        30,
        "sidebar_manual_shoe_bonus"
    )

    manual_stallform_bonus = int_slider(
        "Stallformpoäng per ikryssad häst",
        8,
        0,
        30,
        "sidebar_manual_stallform_bonus"
    )


with st.sidebar.expander("Inaktivitet"):
    inactivity_days_limit = int_slider(
        "Dagar utan start",
        90,
        0,
        365,
        "sidebar_inactivity_days"
    )

    inactivity_penalty = int_slider(
        "Poängavdrag",
        -5,
        -50,
        0,
        "sidebar_inactivity_penalty"
    )


with st.sidebar.expander("Galopp / Kön"):
    scoring_rules["gallop_penalty"] = int_slider(
        "Galoppavdrag",
        scoring_rules["gallop_penalty"],
        -30,
        0,
        "sidebar_gallop_penalty"
    )

    scoring_rules["gallop_penalty_min_count"] = int_slider(
        "Min antal galopper",
        scoring_rules["gallop_penalty_min_count"],
        1,
        5,
        "sidebar_gallop_min"
    )

    scoring_rules["gender_penalty_sto_mixed"] = int_slider(
        "Sto mot hingst/vallack",
        scoring_rules["gender_penalty_sto_mixed"],
        -30,
        0,
        "sidebar_gender_penalty"
    )


with st.sidebar.expander("Tillägg distans"):
    scoring_rules["distance_addition_penalty"]["1640"] = int_slider(
        "1640m per 20m",
        scoring_rules["distance_addition_penalty"]["1640"],
        -40,
        0,
        "sidebar_dist_1640"
    )

    scoring_rules["distance_addition_penalty"]["2140"] = int_slider(
        "2140m per 20m",
        scoring_rules["distance_addition_penalty"]["2140"],
        -40,
        0,
        "sidebar_dist_2140"
    )

    scoring_rules["distance_addition_penalty"]["2640"] = int_slider(
        "2640m+ per 20m",
        scoring_rules["distance_addition_penalty"]["2640"],
        -40,
        0,
        "sidebar_dist_2640"
    )


uploaded_file = st.file_uploader(
    "Ladda upp startlista (.txt eller .docx)",
    type=["txt", "docx"],
    key="main_file_uploader"
)


if uploaded_file is not None:

    if uploaded_file.name.endswith(".txt"):
        file_bytes = uploaded_file.getvalue()

        try:
            raw_data = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raw_data = file_bytes.decode("latin-1")

        raw_data = clean_atg_header(raw_data)

    else:
        raw_data = read_docx(uploaded_file)
        raw_data = clean_atg_header(raw_data)

    races = parse_input(raw_data)

    races = [
        r for r in races
        if r["race"].get("track") != "UNKNOWN"
        and r["race"].get("distance", 0) > 0
        and r["race"].get("start") != "unknown"
    ]

    if not races or any(len(r["horses"]) <= 1 for r in races):
        races = parse_new_atg_format(raw_data)

    races = [
        r for r in races
        if r["race"].get("track") != "UNKNOWN"
        and r["race"].get("distance", 0) > 0
        and r["race"].get("start") != "unknown"
    ]

    st.write("Antal tecken inläst:", len(raw_data))
    st.write("Antal avdelningar hittade:", len(races))

    for race_data in races:
        race = race_data["race"]
        horses = race_data["horses"]

        horses = add_dynamic_scores(horses, race)

        for horse in horses:
            history = horse.get("history", [])

            if history:
                latest_date = history[0].get("date", "")

                try:
                    latest_date_obj = datetime.strptime(latest_date, "%Y-%m-%d")
                    days_since = (datetime.today() - latest_date_obj).days

                    if days_since > inactivity_days_limit:
                        horse["inactivity_score"] = inactivity_penalty
                    else:
                        horse["inactivity_score"] = 0

                except Exception:
                    horse["inactivity_score"] = 0
            else:
                horse["inactivity_score"] = 0

        if not use_spel_percent:
            for horse in horses:
                horse["spel_score"] = 0

        st.subheader(
            f"{race['track']} - Avdelning {race['race_no']} - "
            f"{race['distance']}m ({race['start']})"
        )

        with st.expander(f"Manuell skorjustering - Avdelning {race['race_no']}"):
            cols = st.columns(3)

            for idx, horse in enumerate(horses):
                number = horse.get("number", 0)
                name = horse.get("horse", "")

                checked = cols[idx % 3].checkbox(
                    f"{number} {name}",
                    value=False,
                    key=f"shoe_checkbox_{race['race_no']}_{idx}_{name}"
                )

                horse["shoe_score"] = manual_shoe_bonus if checked else 0

        with st.expander(f"Manuell stallform - Avdelning {race['race_no']}"):
            cols = st.columns(3)

            for idx, horse in enumerate(horses):
                number = horse.get("number", 0)
                name = horse.get("horse", "")

                checked = cols[idx % 3].checkbox(
                    f"{number} {name}",
                    value=False,
                    key=f"stall_checkbox_{race['race_no']}_{idx}_{name}"
                )

                horse["stallform_score"] = manual_stallform_bonus if checked else 0

        for horse in horses:
            horse["total_score"] = calculate_total_score(horse)

        horses = sorted(
            horses,
            key=lambda x: x.get("total_score", 0),
            reverse=True
        )

        rows = []

        for h in horses:
            rows.append({
                "Nr": h.get("number", 0),
                "Spår": h.get("post", 0),
                "Häst": h.get("horse", ""),
                "Tot": h.get("total_score", 0),
                "Speed": h.get("speed_score", 0),
                "AvgTid": h.get("avg_time", ""),
                "Form": h.get("form_score", 0),
                "Stallform": h.get("stallform_score", 0),
                "Senaste": h.get("latest_start_score", 0),
                "Spårpoäng": h.get("post_score", 0),
                "Kusk": h.get("driver_score", 0),
                "Kuskbyte": h.get("driver_change_score", 0),
                "Rek": h.get("record_score", 0),
                "Starter": h.get("starts_score", 0),
                "Seger%": h.get("win_score", 0),
                "Plats%": h.get("place_score", 0),
                "Spel%": h.get("spel_score", 0),
                "Pris": h.get("prize_money_score", 0),
                "Senaste pris": h.get("recent_prize_score", 0),
                "Klass": h.get("class_change_score", 0),
                "Odds": h.get("avg_odds_score", 0),
                "SnittOdds": h.get("avg_odds", ""),
                "Vagn": h.get("wagon_score", 0),
                "Skor": h.get("shoe_score", 0),
                "Inaktiv": h.get("inactivity_score", 0),
                "Manuell": h.get("custom_score", 0),
                "Tillägg": h.get("distance_addition_score", 0),
                "Kön": h.get("gender_score", 0),
                "Galopp": h.get("gallop_score", 0),
                "Prissumma": h.get("prize_money", 0),
                "St": h.get("starts", 0),
                "V%": h.get("win_percent", 0),
                "P%": h.get("place_percent", 0),
                "Spelad %": h.get("percent", 0),
                "Vagn idag": h.get("equipment", ""),
                "Kusk namn": h.get("driver", "")
            })

        df = pd.DataFrame(rows)

        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            column_config={
                "Nr": st.column_config.NumberColumn("Nr", pinned=True),
                "Spår": st.column_config.NumberColumn("Spår", pinned=True),
                "Häst": st.column_config.TextColumn("Häst", pinned=True)
            }
        )