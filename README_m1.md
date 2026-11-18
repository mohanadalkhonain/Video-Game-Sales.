# Video Game Sales — Data Cleaning

Data cleaning component of the video game sales analysis.

Source: `gregorut/videogamesales` on Kaggle (vgsales.csv, VGChartz sales
figures, downloaded via KaggleHub). The raw file is kept unmodified. 
Research questions supported:

1. Which genre + platform combinations sold the most copies in each region?
2. Which genre had the highest total global sales, and did it also have the
   highest average sales per release?
3. For the same genre on the same platform, how did sales compare across
   North America, Europe, and Japan?

## Project structure

```
video_game_sales_project/
├── data/
│   ├── raw/                    # Original downloaded dataset (never modified)
│   └── processed/              # vgsales_cleaned.csv (16,595 rows)
├── outputs/cleaning_reports/   # Audit, cleaning report, review records
├── src/data_cleaning.py        # Reusable Pandas cleaning functions
├── notebooks/                  # Stage A audit scripts (read-only checks)
├── main.py                     # Runs the whole cleaning workflow
└── README.md

## Workflow

1. Load the raw dataset and record "before" statistics.
2. Clean in memory:
   - Remove Rank 16130 (Madden NFL 13, PS3): duplicate game+platform record
     with conflicting sales figures; keep Rank 604.
   - Quarantine Rank 4147 (Sonic the Hedgehog, PS3) to
     `outputs/cleaning_reports/records_requiring_review.csv` — its EU_Sales
     (0.48) conflicts with retained Rank 1717's EU_Sales (0.07), and its
     Year and Publisher are missing. Not deleted.
   - Remove Rank 15002 (Wii de Asobu: Metroid Prime): exact duplicate of
     Rank 15000 in every field except Rank.
   - Convert `Year` to nullable `Int64`, preserving missing values.
   - Validate all sales columns; genuine zeros stay zeros.

Final numbers: **16,598 raw → 16,595 cleaned** (2 removed, 1 quarantined).
Full details in `outputs/cleaning_report
s/cleaning_report.md`.

CSV does not store pandas dtypes, so restore the Year type on load:

```python
import pandas as pd

df = pd.read_csv(
    "data/processed/vgsales_cleaned.csv",
    dtype={"Year": "Int64"},
)
```

## Reports

- `outputs/cleaning_reports/dataset_audit.md` — audit of the raw data.
- `outputs/cleaning_reports/cleaning_report.md` — before/after statistics,
  record-level explanations, sales reconciliation.
- `outputs/cleaning_reports/records_requiring_review.csv`.
