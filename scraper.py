import sys
import os
import json
import csv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from config import API_LINKS, PENALTY_XG, DATA_DIR, CSV_PATH, CSV_FIELDNAMES

sys.stdout.reconfigure(encoding="utf-8")


def _make_driver():
    options = Options()
    options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def _compute_metrics(raw):
    goals        = raw.get("goals", 0)
    xg           = raw.get("expectedGoals", 0.0)
    total_shots  = raw.get("totalShots", 0)
    pens_taken   = raw.get("penaltiesTaken", 0)
    pen_goals    = raw.get("penaltyGoals", 0)
    minutes      = raw.get("minutesPlayed", 0)

    np_shots = total_shots - pens_taken
    npg      = goals - pen_goals
    npxg     = xg - PENALTY_XG * pens_taken
    per90    = minutes / 90 if minutes > 0 else None

    return {
        "Goals":         goals,
        "xG":            round(xg, 2),
        "NP Shots":      np_shots,
        "Minutes":       minutes,
        "NPG":           round(npg, 2),
        "NPG/90":        round(npg / per90, 2) if per90 else 0.0,
        "NPxG":          round(npxg, 2),
        "NPxG/90":       round(npxg / per90, 2) if per90 else 0.0,
        "NPxG Overperf": round(npg - npxg, 2),
        "NP Shot Qual":  round(npxg / np_shots, 2) if np_shots > 0 else 0.0,
        "NP Fin Ratio":  round(npg / np_shots, 2) if np_shots > 0 else 0.0,
    }


def _fetch_league(driver, league_name, url):
    try:
        driver.get(url)
        data = json.loads(driver.find_element(By.TAG_NAME, "pre").text)
        players = []
        for raw in data.get("results", []):
            players.append({
                "ID":     raw.get("player", {}).get("id", ""),
                "League": league_name,
                "Player": raw.get("player", {}).get("name", ""),
                "Team":   raw.get("team", {}).get("name", ""),
                **_compute_metrics(raw),
            })
        print(f"Processed {league_name}: {len(players)} players")
        return players
    except Exception as e:
        print(f"Error fetching {league_name}: {e}")
        return []


def run():
    driver = _make_driver()
    all_players = []

    try:
        for league, url in API_LINKS.items():
            all_players.extend(_fetch_league(driver, league, url))
    finally:
        driver.quit()

    # Sort by NPG desc, then total goals desc, then minutes asc as tiebreaker
    all_players.sort(key=lambda r: (-r["NPG"], -r["Goals"], r["Minutes"]))

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_players)

    print(f"\nSaved {len(all_players)} players to {CSV_PATH}")


if __name__ == "__main__":
    run()
