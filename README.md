# Football Analytics Dashboard

A desktop scouting tool that scrapes live statistics from SofaScore across 12 European leagues, computes advanced non-penalty metrics, and surfaces transfer targets through three customisable recruitment strategies.

---

## Features

- **Live data** — fetches top scorer statistics directly from the SofaScore API via Selenium
- **Advanced metrics** — NPG, NPxG, NPxG/90, NP Shot Quality, NP Finishing Ratio, NPxG Overperformance
- **Three scouting strategies** with configurable filters and a weighted scout score
- **Graph mode** — top 10 players per metric visualised as horizontal bar charts
- **Stats mode** — full sortable table of all players across all leagues
- **Shortlist mode** — filters candidates by age (≤29) and market value (≤15M €), recommends a best buy per strategy

---

## Leagues Covered

Austria · Belgium · Croatia · Czechia · Denmark · Greece · Netherlands · Poland · Portugal · Scotland · Switzerland · Turkey

---

## Project Structure

```
football_analytics/
├── config.py       # League IDs, API URL, constants, file paths
├── scraper.py      # SofaScore fetcher — computes metrics, writes CSV
├── shortlist.py    # Eligibility filters, strategy definitions, scoring functions
├── dashboard.py    # Tkinter UI — graph, stats, and shortlist views
├── data/           # Generated output (CSV written here after first run)
└── requirements.txt
```

---

## Setup

**Prerequisites:** Python 3.10+, Google Chrome, and a matching [ChromeDriver](https://chromedriver.chromium.org/downloads) on your PATH.

```bash
git clone https://github.com/your-username/football-analytics.git
cd football-analytics
pip install -r requirements.txt
```

---

## Usage

Launch the dashboard:

```bash
python dashboard.py
```

Or run the scraper on its own to refresh `data/data.csv`:

```bash
python scraper.py
```

On first launch click **Update Data** in the dashboard — this runs the scraper and populates the CSV before any views can load.

---

## Metrics Reference

| Metric | Formula |
|---|---|
| NPG | Goals − Penalty Goals |
| NPxG | xG − 0.79 × Penalties Taken |
| NPG/90 | NPG ÷ (Minutes ÷ 90) |
| NPxG/90 | NPxG ÷ (Minutes ÷ 90) |
| NPxG Overperf | NPG − NPxG |
| NP Shot Quality | NPxG ÷ NP Shots |
| NP Finishing Ratio | NPG ÷ NP Shots |

---

## Scouting Strategies

| Strategy | Criteria | Scout Score Weights |
|---|---|---|
| The Movement Masters | NPxG Overperf < 0, NPxG/90 > 0.35, NP Shot Qual > 0.2 | Shot Qual 35%, NPxG/90 15%, Overperf 10%, Age 20%, Value 20% |
| The Execution Experts | NPxG Overperf > 2, NP Fin Ratio > 0.2 | Fin Ratio 35%, Overperf 15%, Shot Qual 10%, Age 20%, Value 20% |
| The Volume Vanguards | NPG > 10, NPxG > 10, NPxG/90 > 0.2 | NPG 25%, NPxG 25%, NPxG/90 10%, Age 20%, Value 20% |

All shortlist candidates must be aged 29 or under with a market value below 15M €.

---

## Dependencies

See `requirements.txt`. Key packages: `selenium`, `pandas`, `matplotlib`, `Pillow`.

---

## Disclaimer

This project is for educational and personal use only. Data is sourced from [SofaScore](https://www.sofascore.com). This tool is not affiliated with or endorsed by SofaScore.
