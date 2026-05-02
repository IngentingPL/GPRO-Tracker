# 🏎️ GPRO Tracker

Automatic racing data tracker for [GPRO (Grand Prix Racing Online)](https://gpro.net).

Fetches race data via GPRO API and generates a static dashboard deployed to GitHub Pages.

## Features

- **Overview tab** — Season summary with next race info and standings snapshot
- **Next Race tab** — Step-by-step setup recommendations for the current session (P1→P8→Q1→Q2→Race progression)
- **Practice tab** — Lap-by-lap setup recommendations with driver feedback comments
- **Standings tab** — Current season championship standings
- **Results tab** — Race results per round (qualifying and race positions)
- **Setups tab** — Setup archive per track with weather conditions
- **Finances tab** — Income, costs, and profit per race
- **Driver tab** — Full driver attribute profile with color-coded stats
- **Binary search setup method** — Optimizes setup values based on driver feedback comments
- **Weather and driver attributes** — Setup calculations use track downforce coefficients, temperature adjustments, and driver TI/EXP attributes
- **Automatic GitHub Actions deployment** — Runs twice per week (Tue/Fri 20:30 CET) after races
- **Manual trigger** — Run workflow on-demand via workflow_dispatch

## Setup

### 1. Generate API Token

1. Log in to [app.gpro.net](https://app.gpro.net)
2. Menu → Miscellaneous → API access
3. Copy existing token or generate a new one

### 2. Add GPRO_TOKEN as GitHub Secret

1. In your repository: Settings → Secrets and variables → Actions
2. New repository secret
3. Name: `GPRO_TOKEN`
4. Value: your API token

### 3. Enable GitHub Pages

1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main`, folder: `/ (root)`

### 4. Done!

The workflow automatically fetches data after each race (Tue/Fri at 20:30 CET).
You can also run it manually: Actions → Fetch GPRO Data & Deploy → Run workflow.

## Manual Usage

```bash
export GPRO_TOKEN="your_token"

# Fetch practice data (during race week)
python gpro_fetcher.py --mode current-week

# Fetch post-race data (after race)
python gpro_fetcher.py

# Generate predictions
python predictor.py

# Generate dashboard
python generate_dashboard.py
```

## Project Structure

```
GPRO-Tracker/
├── gpro_fetcher.py        # Fetches data from GPRO API (two modes)
├── predictor.py           # Generates setup recommendations
├── generate_dashboard.py # Generates HTML dashboard
├── index.html            # Generated dashboard (do not edit)
├── data/
│   ├── races/            # Per-race JSON files (S{season}R{race}.json)
│   ├── prediction.json   # Current setup predictions
│   ├── calendar.json     # Season calendar
│   └── current_context.json  # Current race context
├── .github/workflows/fetch.yml
├── CHANGELOG.md
├── CLAUDE.md
└── README.md
```

## Requirements

- Python 3.8+ (no external libraries required)
- GPRO account with API token

## Notes

- API request count per run (~7 post-race, ~3 current-week)
- Data stored as JSON for future analysis
- Dashboard works offline — data embedded in HTML
- Do not edit index.html directly — it is regenerated on every run