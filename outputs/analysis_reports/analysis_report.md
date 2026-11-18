# Video Game Sales — Data Analysis Report (Member 2)

**Dataset:** `data/processed/vgsales_cleaned.csv` (16,595 releases, cleaned by Member 1)
**Code:** `src/analysis.py`, `run_analysis.py`, `compare_before_after.py` (step-by-step history in `outputs/analysis_reports/work_log.md`)
**Tools:** pandas, NumPy

Sales figures are in millions of copies.

---

## 1. How the analysis is built

### Classes and polymorphism

| Class | What `run(data)` does |
|---|---|
| `SalesAnalysis` | Base class. `run(data)` raises `NotImplementedError`, so every subclass must override it. |
| `GenreSummary` | Groups releases by genre and returns total and average global sales, plus the genre's rank by average (`avg_rank`). Answers Q2. |
| `RegionalComparison` | Builds the NumPy sales matrix and the per-pair regional totals, then returns the best-selling genre–platform pair in each region. Answers Q1 and supplies the data for Q3. |

`run_analysis.py` calls `run(data)` on both objects in one loop:

```python
for obj in [GenreSummary(), RegionalComparison()]:
    print(obj.run(data))
```

The call is the same, but each class returns a different result. This is the polymorphism demo.

### NumPy matrix and the marker-vector multiplication

1. **Sales matrix.** `M = data[REGIONS].to_numpy()` stores the four regional columns (`NA_Sales`, `EU_Sales`, `JP_Sales`, `Other_Sales`). It has one row per release, so its shape is **16,595 × 4**.
2. **Totals and averages per region.** `M.sum(axis=0)` gives total sales per region, and `M.mean(axis=0)` gives average sales per release.
3. **Marker vector.** For each of the **293** genre–platform pairs, `v` has one entry per release: 1 if the release belongs to the pair, 0 if not.
   ```python
   v = ((data["Genre"] == g) & (data["Platform"] == p)).to_numpy().astype(int)
   ```
4. **Matrix multiplication.** `v @ M` has shape (16,595,) @ (16,595 × 4), which gives a vector of 4 numbers: the pair's total sales in each region. The 0 entries cancel every release outside the pair.
   *Example:* for Shooter on X360, `v` marks 203 releases and `v @ M` = `[174.22, 76.59, 3.10, 24.53]`.
5. **Self-check.** The code asserts that the matrix results equal pandas `groupby(["Genre", "Platform"]).sum()` and that the sales matrix has no missing values. Both checks pass.

---

## 2. Results

### Sales by region (NumPy)

| Region | Total sales | Average per release |
|---|---|---|
| North America | 4,392.95 | 0.265 |
| Europe | 2,433.64 | 0.147 |
| Japan | 1,291.00 | 0.078 |
| Other | 797.75 | 0.048 |

North America accounts for about half of all sales (49%). Europe accounts for 27%, Japan for 14% and Other for 9%.

### Q1 — Which genre–platform combinations sold the most in each region?

| Region | Best genre–platform pair | Sales |
|---|---|---|
| North America | Shooter on X360 | 174.22 |
| Europe | Action on PS3 | 110.62 |
| Japan | Role-Playing on DS | 54.55 |
| Other | Action on PS2 | 47.64 |

Each region has a different winner. North America favours shooters on Xbox, Europe and the rest of the world favour action games on PlayStation, and Japan favours role-playing games on a Nintendo handheld.

### Q2 — Which genre had the highest total global sales? Did it also have the highest average per release?

| Genre | Total | Average per release | Rank by average |
|---|---|---|---|
| **Action** | **1,751.18** (1st) | 0.528 | 7 |
| Sports | 1,330.92 | 0.568 | 5 |
| Shooter | 1,037.35 | 0.792 | 2 |
| Role-Playing | 927.37 | 0.623 | 3 |
| **Platform** | 830.89 | **0.939** (1st) | 1 |
| Misc | 809.96 | 0.466 | 8 |
| Racing | 732.04 | 0.586 | 4 |
| Fighting | 448.91 | 0.529 | 6 |
| Simulation | 392.20 | 0.452 | 9 |
| Puzzle | 244.95 | 0.421 | 10 |
| Adventure | 239.04 | 0.186 | 12 |
| Strategy | 175.12 | 0.257 | 11 |

**Answer:** Action had the highest total global sales (1,751.18M), but it did **not** have the highest average per release. Action ranks only 7th of 12 by average. Platform games have the highest average (0.94M per release), followed by Shooter (0.79M).

Action's high total comes from the large number of Action releases, not from strong sales per game.

### Q3 — For the same genre on the same platform, how did sales compare across North America, Europe and Japan?

Top 10 genre–platform pairs by combined NA + EU + JP sales:

| Genre | Platform | NA | EU | JP | NA % | EU % | JP % |
|---|---|---|---|---|---|---|---|
| Sports | Wii | 151.77 | 94.99 | 18.25 | 57.3 | 35.8 | 6.9 |
| Action | PS3 | 121.16 | 110.62 | 29.59 | 46.4 | 42.3 | 11.3 |
| Shooter | X360 | 174.22 | 76.59 | 3.10 | 68.6 | 30.2 | 1.2 |
| Sports | PS2 | 134.12 | 69.96 | 24.74 | 58.6 | 30.6 | 10.8 |
| Action | PS2 | 127.82 | 71.44 | 25.81 | 56.8 | 31.7 | 11.5 |
| Action | X360 | 141.39 | 76.81 | 2.77 | 64.0 | 34.8 | 1.3 |
| Misc | Wii | 121.49 | 65.57 | 14.48 | 60.3 | 32.5 | 7.2 |
| Shooter | PS3 | 81.88 | 75.14 | 8.81 | 49.4 | 45.3 | 5.3 |
| Racing | PS2 | 75.72 | 47.38 | 5.92 | 58.7 | 36.7 | 4.6 |
| Misc | DS | 54.99 | 35.65 | 37.33 | 43.0 | 27.9 | 29.2 |

Pairs where North America is **not** the leading region (among the 101 pairs with at least 20M combined NA+EU+JP sales):

| Leading region | Example pairs (NA / EU / JP) |
|---|---|
| Japan (14 pairs) | Role-Playing on DS (47.46 / 18.30 / 54.55), Role-Playing on 3DS (20.18 / 13.00 / 39.61), Role-Playing on PSP (11.42 / 3.76 / 30.82) |
| Europe (10 pairs) | Action on PS4 (29.70 / 38.19 / 5.41), Racing on PS3 (23.86 / 33.86 / 3.13), Simulation on PC (19.94 / 27.37 / 0.00) |

**Findings:**

- North America leads in most pairs.
- **Xbox 360 games barely sell in Japan.** Shooter on X360 and Action on X360 each earn about 1% of their NA+EU+JP sales there.
- **Japan prefers role-playing games on Nintendo and Sony handhelds.** 27% of Japan's sales are Role-Playing, compared with about 8% in North America and Europe.
- **Europe is strongest on newer PlayStation consoles (PS4) and PC**, where it often beats North America.

---

## 3. Effect of data cleaning (before vs after)

`compare_before_after.py` runs the same analysis on the raw and the cleaned data.

| | Raw | Cleaned |
|---|---|---|
| Rows | 16,598 | 16,595 |
| Global sales | 8,920.44 | 8,919.93 (−0.51) |

Member 1 took 3 records out of the cleaned data:

- Two duplicate records were removed: Rank 15002 (Wii de Asobu: Metroid Prime) and Rank 16130 (Madden NFL 13, PS3).
- One conflicting record was quarantined for review: Rank 4147 (Sonic the Hedgehog, PS3).

**Impact on results:**

- **Q1:** the best pair in every region is unchanged, with identical sales.
- **Q2:** Action is still highest by total and Platform is still highest by average. Every genre's rank is the same.
- Only Platform, Sports and Shooter changed, each by 0.48M or less (under 0.01% of total sales).

The cleaning removed duplicates without changing any finding, so the results are reliable.

---

## 4. Recommendations for the marketing team

- **North America:** shooters and action games on Xbox and PlayStation sell the most. Target this market first for those genres.
- **Europe:** action, racing and shooter games on PlayStation and PC. On PS4 and PC, Europe often outsells North America.
- **Japan:** role-playing games on Nintendo and Sony handhelds. Xbox titles are not worth localising for Japan.
- **Genre choice:** Platform and Shooter games sell the most per release. Action sells the most in total but faces heavy competition from a large number of releases.

## 5. Limitations

- Sales are VGChartz estimates up to about 2016, so newer platforms (PS4, Xbox One) have incomplete histories.
- The dataset only includes games with at least about 0.01M in sales.
- 269 releases have no Year and 57 have no Publisher. This analysis uses neither column, so the results are unaffected.

## How to run

```bash
python run_analysis.py          # all results for Q1-Q3
python compare_before_after.py  # raw vs cleaned comparison
```
