# Work Log — Data Analysis (Member 2)

This log records, step by step, how the analysis part of the project was built: what was done at each stage, why, and what came out of it.
The final results are in `analysis_report.md`, in the same folder.

---

## Step 1 — Understand the task and the dataset

**What we did**

- Read the project plan:
  - three research questions
  - three team roles: cleaning, analysis, visualization
  - the target user, a game publisher's marketing team
- Opened `vgsales.csv` (Kaggle `gregorut/videogamesales`) and checked its columns: `Rank, Name, Platform, Year, Genre, Publisher, NA_Sales, EU_Sales, JP_Sales, Other_Sales, Global_Sales`.
- Identified the **four regional sales columns**: `NA_Sales` (North America), `EU_Sales` (Europe), `JP_Sales` (Japan) and `Other_Sales` (rest of world).
  - `Global_Sales` is their sum, so it is **not** a region.
  - Q3 only compares North America, Europe and Japan.

**Decision:** keep the region list in one constant so every part of the code uses the same columns:
```python
REGIONS = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]
```

## Step 2 — Start before the cleaned data was ready

**Problem:** Member 1 was still cleaning the data.

**What we did**

- Developed on the raw CSV with a temporary minimal clean:
  ```python
  data = pd.read_csv("vgsales.csv").dropna(subset=["Genre", "Platform"])
  ```
- Designed every analysis method to take a DataFrame as input instead of a hard-coded file. That way, switching to the cleaned file later only needs a one-line change.
- Agreed to keep the original column names, so Member 1's output would plug straight in.

## Step 3 — Design the classes (polymorphism)

**What we did**

- Created a base class `SalesAnalysis` with a `run(data)` method that raises `NotImplementedError`. This forces every subclass to override it.
- Created two subclasses:
  - `GenreSummary.run(data)` returns total and average global sales by genre (Q2).
  - `RegionalComparison.run(data)` returns the best-selling genre–platform pair in each region (Q1).
- Wrote one loop that calls `run(data)` on both objects:
  ```python
  for obj in [GenreSummary(), RegionalComparison()]:
      print(obj.run(data))
  ```
  The same method call produces different results depending on the object's class. This is the polymorphism demonstration.
- Every `run` returns a pandas DataFrame, so Member 3 can chart the results directly.

## Step 4 — GenreSummary (Q2)

**What we did**

```python
data.groupby("Genre")["Global_Sales"].agg(total="sum", average="mean").sort_values("total", ascending=False)
```

This works as a four-step pipeline:

1. `groupby("Genre")` splits the rows by genre.
2. `["Global_Sales"]` keeps only the sales column.
3. `.agg(total="sum", average="mean")` calculates two named columns.
4. `.sort_values(...)` puts the largest total first.

**Result:** Action has the highest total, but Platform has the highest average per release.

## Step 5 — Make the code answer Q2 directly

**What we did**

- Added code that names the winners with `idxmax()` and prints whether they are the same genre:
  ```python
  g["total"].idxmax()    # → Action
  g["average"].idxmax()  # → Platform
  ```
- Added an `avg_rank` column, so each genre shows its position by average (1 = highest):
  ```python
  out["avg_rank"] = out["average"].rank(ascending=False).astype(int)
  ```

**Correction made:** a hand count had placed Action 8th by average. The `avg_rank` column showed it is actually **7th**. We kept the code's value.

## Step 6 — NumPy matrix and the marker-vector multiplication (Q1)

This step implements the method from the project plan.

**What we did (inside `RegionalComparison.run`)**

1. **Sales matrix:** `M = data[REGIONS].to_numpy()` has one row per release and one column per region, so its shape is **16,595 × 4**.
2. **Region totals and averages:** `M.sum(axis=0)` and `M.mean(axis=0)` are stored in `region_stats`.
3. **Marker vector for each genre–platform pair:** 1 if the release belongs to the pair, 0 if not.
   ```python
   v = ((data["Genre"] == g) & (data["Platform"] == p)).to_numpy().astype(int)
   ```
4. **Matrix multiplication:** `v @ M` gives that pair's four regional totals. The 0 entries cancel every release outside the pair.
   - Example, Shooter on X360: 203 releases → `[174.22, 76.59, 3.10, 24.53]`.
5. Repeated for all **293** genre–platform pairs and collected into the `pair_sales` table. Then `idxmax()` picks the best pair in each region.

**Self-checks added**

- `assert not np.isnan(M).any()` confirms there are no missing sales values.
- An `assert` that the `v @ M` results equal pandas `groupby(["Genre", "Platform"]).sum()` confirms the matrix method is correct.

## Step 7 — Switch to the cleaned data

**What we did**

- When Member 1 delivered `vgsales_cleaned.csv`, we changed only the file path and removed the temporary `dropna`.
- Inspected the cleaned file:
  - same 11 columns and same column names
  - 16,595 rows, compared with 16,598 raw
- Confirmed that the rows still in the cleaned file are identical to the raw rows.
- Both self-checks still pass.

**What the cleaning changed:**

- 2 duplicate records were removed: Wii de Asobu: Metroid Prime (Wii) and Madden NFL 13 (PS3).
- 1 conflicting record, Sonic the Hedgehog (PS3), was moved to a review file.
- The cleaned file still has 269 missing Year values and 57 missing Publisher values. The analysis uses neither column.

**Correction made:** we first described all 3 records as duplicates. Member 1's cleaning notes show that Sonic was quarantined because of conflicting data, not removed as a duplicate.

## Step 8 — Compare results before vs after cleaning

**What we did**

Wrote `compare_before_after.py`, which runs the same analysis on the raw and the cleaned data side by side.

| | Raw | Cleaned |
|---|---|---|
| Rows | 16,598 | 16,595 |
| Global sales (M) | 8,920.44 | 8,919.93 (−0.51) |
| Q1 best pair per region | same | same |
| Q2 highest total / highest average | Action / Platform | Action / Platform |
| Genre ranks | — | unchanged |

**Conclusion:** the cleaning removed less than 0.01% of sales and changed no finding.

## Step 9 — Q3 comparison (NA vs EU vs JP)

**What we did**

- Used the `pair_sales` table from Step 6 and took the top 10 genre–platform pairs by combined NA + EU + JP sales.
- Calculated each region's share of those sales (%).
- Counted the pairs where Europe or Japan, not North America, sell the most.

**Result:**

- North America leads most pairs.
- Japan leads in 14 large pairs, mostly role-playing games on handhelds.
- Europe leads in 10 pairs, mostly on PS4 and PC.
- Xbox 360 games sell about 1% of their copies in Japan.

## Step 10 — Package everything for the team

**What we did**

- Organised the files into the repository:

| File | Purpose |
|---|---|
| `src/analysis.py` | The classes, the region list and the data paths |
| `run_analysis.py` | Prints the answers to Q1, Q2 and Q3 |
| `compare_before_after.py` | Compares results on raw vs cleaned data |
| `data/raw/vgsales.csv` | Original dataset |
| `data/processed/vgsales_cleaned.csv` | Member 1's cleaned dataset |
| `outputs/analysis_reports/analysis_report.md` | Results report |
| `outputs/analysis_reports/work_log.md` | This log |

- Ran both scripts from the repository to confirm they work.

---

## Summary

| Question | Answer |
|---|---|
| **Q1** Best genre–platform per region | NA: Shooter / X360 (174.22M) · EU: Action / PS3 (110.62M) · JP: Role-Playing / DS (54.55M) · Other: Action / PS2 (47.64M) |
| **Q2** Highest total vs highest average | Highest total: Action (1,751.18M). Highest average: Platform (0.94M per release). Not the same genre; Action is 7th by average. |
| **Q3** NA vs EU vs JP for the same pair | NA leads most pairs; Japan leads handheld role-playing games; Europe leads on PS4 and PC; Xbox barely sells in Japan |

## How to run

```bash
pip install pandas numpy
python run_analysis.py
python compare_before_after.py
```
