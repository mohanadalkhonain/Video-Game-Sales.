# Video Game Sales — Data Cleaning

Data cleaning component of the video game sales analysis: it loads the raw
dataset, applies the approved cleaning decisions, and produces a cleaned CSV
suitable for the Pandas/NumPy analysis and the Matplotlib/Seaborn
visualizations.

Source: `vgsales.csv` from Kaggle (`gregorut/videogamesales`, VGChartz sales
figures), downloaded manually. The raw file is kept unmodified in
`data/raw/`.

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
├── requirements.txt
└── README.md
```

## How to run

Run the commands from the project folder (all file paths are relative):

```bash
py -m pip install -r requirements.txt   # pandas
py main.py
```

Before running, download the dataset manually from Kaggle
(`https://www.kaggle.com/datasets/gregorut/videogamesales`) and place it at
`data/raw/vgsales.csv`. The program stops with a clear error message if the
file is missing, and never overwrites the raw file.

## Workflow

1. Load the raw dataset and record "before" statistics.
2. Clean in memory, applying only the approved decisions:
   - Remove Rank 16130 (Madden NFL 13, PS3): duplicate game+platform record
     with conflicting sales figures; keep Rank 604.
   - Quarantine Rank 4147 (Sonic the Hedgehog, PS3, Genre Platform) to
     `outputs/cleaning_reports/records_requiring_review.csv` — its EU_Sales
     (0.48) conflicts with retained Rank 1717's EU_Sales (0.07), and its
     Year and Publisher are missing. Not deleted.
   - Remove Rank 15002 (Wii de Asobu: Metroid Prime): exact duplicate of
     Rank 15000 in every field except Rank.
   - Convert `Year` to nullable `Int64`, preserving missing values.
   - Validate all sales columns; genuine zeros stay zeros.
   - Remove U+200B ZERO WIDTH SPACE from text columns (approved rule):
     one invisible character was found at the end of Rank 11595's Name,
     inherited from the Kaggle source. Only U+200B is removed — every other
     Unicode character and all other text is preserved exactly.
3. Validate in memory before writing anything.
4. Snapshot the current outputs in memory, then save the cleaned CSV, the
   quarantined record and the full before/after cleaning report.
5. Reload the saved files and verify their actual contents (rows, columns,
   Rank, sales values, missing Years, Int64 load, quarantined record vs the
   raw record). If verification fails, the previous outputs are restored —
   existing files are overwritten only after every check passes.

Final numbers: **16,598 raw → 16,595 cleaned** (2 removed, 1 quarantined).
Full details in `outputs/cleaning_reports/cleaning_report.md`.

## Loading the cleaned dataset

CSV does not store pandas dtypes, so restore the Year type on load:

```python
import pandas as pd

df = pd.read_csv(
    "data/processed/vgsales_cleaned.csv",
    dtype={"Year": "Int64"},
)
```

Notes on the cleaned dataset:

- Column names and case are unchanged (11 columns); nothing was aggregated.
- Missing `Year` (269 rows) and missing `Publisher` (57 rows) are preserved
  as missing — never filled or zeroed.
- Four records dated 2017/2020 are retained with their source-provided Year
  values; they have not been independently verified and exceed most of the
  dataset's time range (2016 is not a confirmed coverage cutoff). They do
  not change any leading result (checked in Stage A).
- `Global_Sales` was never recalculated; the largest difference between it
  and the sum of the four regions is 0.02M (rounding to 2 decimals).
- Zeros in sales columns are genuine sales information, not missing data.

## Reports

- `outputs/cleaning_reports/dataset_audit.md` — audit of the raw data.
- `outputs/cleaning_reports/cleaning_report.md` — before/after statistics,
  record-level explanations, sales reconciliation, limitations.
- `outputs/cleaning_reports/records_requiring_review.csv` — quarantined
  record kept for human review.
