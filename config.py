import os

# League IDs and season IDs from SofaScore
LEAGUES = {
    "Austria":     {"id": 45,  "season": 77382},
    "Belgium":     {"id": 38,  "season": 77040},
    "Croatia":     {"id": 170, "season": 76980},
    "Czechia":     {"id": 172, "season": 77019},
    "Denmark":     {"id": 39,  "season": 76491},
    "Greece":      {"id": 185, "season": 78175},
    "Netherlands": {"id": 37,  "season": 77012},
    "Poland":      {"id": 202, "season": 76477},
    "Portugal":    {"id": 238, "season": 77806},
    "Scotland":    {"id": 36,  "season": 77128},
    "Switzerland": {"id": 215, "season": 77152},
    "Turkey":      {"id": 52,  "season": 77805},
}

_STATS_URL = (
    "https://www.sofascore.com/api/v1/unique-tournament/{id}/season/{season}"
    "/statistics?limit=20&order=-goals&accumulation=total"
    "&fields=goals%2CexpectedGoals%2CtotalShots%2CpenaltiesTaken%2CpenaltyGoals%2CminutesPlayed"
    "&filters=position.in.G~D~M~F"
)

# Pre-built API links keyed by country name
API_LINKS = {
    country: _STATS_URL.format(**data)
    for country, data in LEAGUES.items()
}

# xG credit assigned to each penalty taken
PENALTY_XG = 0.79

# Output CSV location
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(DATA_DIR, "data.csv")

# Column order written to CSV (ID kept for shortlist lookups but hidden in UI)
CSV_FIELDNAMES = [
    "ID", "League", "Player", "Team", "Minutes",
    "Goals", "NPG", "NPG/90", "xG", "NPxG", "NPxG/90",
    "NPxG Overperf", "NP Shots", "NP Shot Qual", "NP Fin Ratio",
]
