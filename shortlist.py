import json
import time
from datetime import datetime

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Base eligibility thresholds
MAX_AGE            = 29
MAX_MARKET_VALUE_M = 15
MIN_MINUTES        = 900

# Strategy definitions: display label, criteria string, and filter predicate
STRATEGIES = {
    "The Movement Masters": {
        "criteria": "NPxG Overperf < 0, NPxG/90 > 0.35, NP Shot Qual > 0.2",
        "filter":   lambda r: r["NPxG Overperf"] < 0 and r["NPxG/90"] > 0.35 and r["NP Shot Qual"] > 0.2,
    },
    "The Execution Experts": {
        "criteria": "NPxG Overperf > 2, NP Fin Ratio > 0.2",
        "filter":   lambda r: r["NPxG Overperf"] > 2 and r["NP Fin Ratio"] > 0.2,
    },
    "The Volume Vanguards": {
        "criteria": "NPG > 10, NPxG > 10, NPxG/90 > 0.2",
        "filter":   lambda r: r["NPG"] > 10 and r["NPxG"] > 10 and r["NPxG/90"] > 0.2,
    },
}

# Scoring formula hints shown in the UI
SCORE_HINTS = {
    "The Movement Masters":  "NP Shot Qual 35%, NPxG/90 15%, NPxG Overperf 10%, Age 20%, Value 20%",
    "The Execution Experts": "NP Fin Ratio 35%, NPxG Overperf 15%, NP Shot Qual 10%, Age 20%, Value 20%",
    "The Volume Vanguards":  "NPG 25%, NPxG 25%, NPxG/90 10%, Age 20%, Value 20%",
}


# --- Helper functions ---

def _parse_age(dob_string):
    try:
        dob   = datetime.fromisoformat(dob_string.replace("Z", "+00:00"))
        today = datetime.now()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return None


def _format_value(value_raw):
    if not value_raw:
        return "N/A"
    return f"{value_raw / 1_000_000:.1f}M €"


def _age_component(age):
    return 100 - (age - 18) * 9


def _value_component(value_m):
    return 100 - (value_m / MAX_MARKET_VALUE_M) * 100


# --- Per-strategy scoring functions ---

def _score_movement_master(p):
    return (
        35 * min(1.0, p["NP Shot Qual"]  / 0.25) +
        15 * min(1.0, p["NPxG/90"]       / 0.60) +
        10 * min(1.0, abs(min(0, p["NPxG Overperf"])) / 3) +
        0.20 * _age_component(p["Age"]) +
        0.20 * _value_component(p["Market Value Raw"])
    )


def _score_execution_expert(p):
    return (
        35 * min(1.0, p["NP Fin Ratio"]          / 0.25) +
        15 * min(1.0, max(0, p["NPxG Overperf"]) / 5.0) +
        10 * min(1.0, p["NP Shot Qual"]           / 0.20) +
        0.20 * _age_component(p["Age"]) +
        0.20 * _value_component(p["Market Value Raw"])
    )


def _score_volume_vanguard(p):
    return (
        25 * min(1.0, p["NPG"]      / 20) +
        25 * min(1.0, p["NPxG"]     / 20) +
        10 * min(1.0, p["NPxG/90"]  / 0.5) +
        0.20 * _age_component(p["Age"]) +
        0.20 * _value_component(p["Market Value Raw"])
    )


_SCORERS = {
    "The Movement Masters":  _score_movement_master,
    "The Execution Experts": _score_execution_expert,
    "The Volume Vanguards":  _score_volume_vanguard,
}


def best_buy(strategy_name, players):
    if not players:
        return None, None
    scorer = _SCORERS[strategy_name]
    best   = max(players, key=scorer)
    return best, round(scorer(best), 2)


# --- Main shortlist builder ---

def build_shortlist(df):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)

    shortlist = {name: [] for name in STRATEGIES}

    try:
        for _, row in df.iterrows():
            try:
                driver.get(f"https://api.sofascore.com/api/v1/player/{row['ID']}")
                player_data = json.loads(
                    driver.find_element(By.TAG_NAME, "pre").text
                ).get("player", {})

                age       = _parse_age(player_data.get("dateOfBirth"))
                value_obj = player_data.get("proposedMarketValueRaw")
                value_raw = value_obj.get("value") if isinstance(value_obj, dict) else None
                value_m   = value_raw / 1_000_000 if value_raw else None

                # Base eligibility filters
                if age is None or age > MAX_AGE:
                    continue
                if value_m is None or value_m > MAX_MARKET_VALUE_M:
                    continue
                if pd.isna(row["Minutes"]) or row["Minutes"] <= MIN_MINUTES:
                    continue

                player_info = {
                    "Player":          row["Player"],
                    "Team":            row["Team"],
                    "Age":             age,
                    "Market Value":    _format_value(value_raw),
                    "Market Value Raw": value_m,
                    "NPxG Overperf":   row["NPxG Overperf"],
                    "NPxG/90":         row["NPxG/90"],
                    "NP Shot Qual":    row["NP Shot Qual"],
                    "NP Fin Ratio":    row["NP Fin Ratio"],
                    "NPG":             row["NPG"],
                    "NPxG":            row["NPxG"],
                    "Minutes":         int(row["Minutes"]),
                }

                for name, strategy in STRATEGIES.items():
                    if strategy["filter"](row):
                        shortlist[name].append(player_info)

                time.sleep(0.25)

            except Exception:
                continue
    finally:
        driver.quit()

    return shortlist
