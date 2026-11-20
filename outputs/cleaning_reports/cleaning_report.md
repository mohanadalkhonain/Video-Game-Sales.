# Cleaning Report - Video Game Sales

Source: `data/raw/vgsales.csv`.
Outputs: `data/processed/vgsales_cleaned.csv`, `records_requiring_review.csv`.

## 1. Before / after summary

| Metric | Before (raw) | After (cleaned) |
|---|---|---|
| Row count | 16598 | 16595 |
| Exact duplicate rows | 0 | 0 |
| Duplicate Name+Platform combinations | 5 | 2 (remaining pairs are different-year releases of the same title: legitimate) |
| Year column type | float64 | `Int64` |

### Missing values before vs after

| Column | Before | After | Why it moved |
|---|---|---|---|
| Rank | 0 | 0 | unchanged |
| Name | 0 | 0 | unchanged |
| Platform | 0 | 0 | unchanged |
| Year | 271 | 269 | quarantined Rank 4147 (missing Year) and removed Rank 15002 (missing Year) |
| Genre | 0 | 0 | unchanged |
| Publisher | 58 | 57 | quarantined Rank 4147 (missing Publisher) |
| NA_Sales | 0 | 0 | unchanged |
| EU_Sales | 0 | 0 | unchanged |
| JP_Sales | 0 | 0 | unchanged |
| Other_Sales | 0 | 0 | unchanged |
| Global_Sales | 0 | 0 | unchanged |

## 2. Record-level explanation of every affected row

Every removed or quarantined row is shown exactly as it appeared in the original data. Row numbers are pandas positional indices, where 0 is the first data row; the equivalent 1-based CSV line (including the header) is index + 2.

### Removed - Rank 15002
- **Reason:** Wii de Asobu: Metroid Prime (Wii): exact duplicate of Rank 15000 - all fields including every sales value are identical; only Rank differs. Retained: Rank 15000. Zero information loss.
- **Actual effect on sales totals, summed directly from the original CSV:** NA_Sales 0.00M, EU_Sales 0.00M, JP_Sales 0.02M, Other_Sales 0.00M, Global_Sales 0.02M.
- Row as it appeared in the raw data (pandas row index 14999; CSV line 15001 with the header included):
```
Rank                                  15002
Name            Wii de Asobu: Metroid Prime
Platform                                Wii
Year                                    NaN
Genre                               Shooter
Publisher                          Nintendo
NA_Sales                                0.0
EU_Sales                                0.0
JP_Sales                               0.02
Other_Sales                             0.0
Global_Sales                           0.02
```

### Removed - Rank 16130
- **Reason:** Madden NFL 13 (PS3): duplicate game+platform record with conflicting sales figures (NOT an exact duplicate). A self-consistent partial tracking entry (Global 0.01M, all regions ~0) separate from the complete record at Rank 604. Kept: Rank 604. Sales effect of removal is calculated from the original CSV in the cleaning report.
- **Actual effect on sales totals, summed directly from the original CSV:** NA_Sales 0.00M, EU_Sales 0.01M, JP_Sales 0.00M, Other_Sales 0.00M, Global_Sales 0.01M.
- Row as it appeared in the raw data (pandas row index 16127; CSV line 16129 with the header included):
```
Rank                      16130
Name              Madden NFL 13
Platform                    PS3
Year                     2012.0
Genre                    Sports
Publisher       Electronic Arts
NA_Sales                    0.0
EU_Sales                   0.01
JP_Sales                    0.0
Other_Sales                 0.0
Global_Sales               0.01
```

### Quarantined (NOT deleted) - Rank 4147
- **Reason:** Sonic the Hedgehog (PS3): conflicting sales figures versus retained Rank 1717 (EU_Sales 0.48 vs 0.07 - two records cannot both be right about the same quantity), and incomplete metadata (missing Year AND Publisher). Kept as a full record for review here; NOT deleted. Retained record: Rank 1717.
- **Potential effect on regional totals if ever re-added:** adds NA 0.00M, EU 0.48M, JP 0.00M, Other 0.00M, Global 0.48M (EU total would rise by 0.48M and the Platform/PS3 EU combination would gain 0.48M - it is kept out of the primary dataset until reviewed because its EU figure contradicts Rank 1717's 0.07M).
- **Platform verification (evidence-based review):** both records were checked directly against the raw data. Rank 1717 is the same game on the SAME platform as Rank 4147: Sonic the Hedgehog, PS3, Year 2006, Genre Platform, Publisher Sega, sales NA 0.41 / EU 0.07 / JP 0.04 / Other 0.66 / Global 1.18. Comparing the two PS3 records' sales is therefore valid: one title on one platform should not appear twice with different figures.
- **Record-shape context:** Rank 4147 carries a single nonzero regional figure (EU 0.48) with all other regions at 0.0, plus missing Year AND Publisher - the same partial-tracking-entry pattern as Rank 16130 (Madden NFL 13), not a complete release record. The 1991 Genesis original (Rank 255) and the 2006 X360 release (Rank 1985) are separate, legitimate releases on different platforms and are not part of this duplicate pair.
- **Decision re-checked:** the quarantine reasons stand as verified (same title + same platform duplicate with inconsistent figures, and missing Year and Publisher); the record remains quarantined, its status unchanged.
- Row as it appeared in the raw data (pandas row index 4145; CSV line 4147 with the header included):
```
Rank                          4147
Name            Sonic the Hedgehog
Platform                       PS3
Year                           NaN
Genre                     Platform
Publisher                      NaN
NA_Sales                       0.0
EU_Sales                      0.48
JP_Sales                       0.0
Other_Sales                    0.0
Global_Sales                  0.48
```

### Cleaned in place (record kept) - Rank 11595 (Name: U+200B removed)

- **What:** the end of the `Name` field carried a U+200B ZERO WIDTH SPACE, an invisible Unicode format character (category Cf) that cannot be seen when the text is viewed normally. It appears in `repr()` as `\u200b`.
- **Origin:** the character was present in the original Kaggle dataset (`gregorut/videogamesales`) and passed through the earlier cleaning stages untouched.
- **Rule applied:** the cleaning workflow now removes U+200B from the text columns via `remove_zero_width_spaces()`. Only U+200B is removed: no other Unicode character, no whitespace strip and no case change - every other character of the text, legitimate Unicode included, is preserved exactly.
- `Name` before (repr view): `'Boku no Natsuyasumi 3: Hokkoku Hen: Chiisana Boku no Dai Sougen\u200b'`
- `Name` after  (repr view): `'Boku no Natsuyasumi 3: Hokkoku Hen: Chiisana Boku no Dai Sougen'`
- **All other fields of this record are unchanged** from the raw data.

## 3. Sales reconciliation (before vs after)

Check: raw total = cleaned total + quarantined + removed. A difference of 0.00 proves no sales value was created, modified or lost during cleaning.

| Column | Raw total | Cleaned total | Quarantined | Removed | Difference |
|---|---|---|---|---|---|
| NA_Sales | 4392.95 | 4392.95 | 0.00 | 0.00 | 0.00 |
| EU_Sales | 2434.13 | 2433.64 | 0.48 | 0.01 | 0.00 |
| JP_Sales | 1291.02 | 1291.00 | 0.00 | 0.02 | 0.00 |
| Other_Sales | 797.75 | 797.75 | 0.00 | 0.00 | 0.00 |
| Global_Sales | 8920.44 | 8919.93 | 0.48 | 0.03 | 0.00 |

## 4. Actions applied (in order)

- **[quarantined] Rank 4147** - Sonic the Hedgehog (PS3): conflicting sales figures versus retained Rank 1717 (EU_Sales 0.48 vs 0.07 - two records cannot both be right about the same quantity), and incomplete metadata (missing Year AND Publisher). Kept as a full record for review here; NOT deleted. Retained record: Rank 1717.
- **[removed] Rank 16130** - Madden NFL 13 (PS3): duplicate game+platform record with conflicting sales figures (NOT an exact duplicate). A self-consistent partial tracking entry (Global 0.01M, all regions ~0) separate from the complete record at Rank 604. Kept: Rank 604. Sales effect of removal is calculated from the original CSV in the cleaning report.
- **[removed] Rank 15002** - Wii de Asobu: Metroid Prime (Wii): exact duplicate of Rank 15000 - all fields including every sales value are identical; only Rank differs. Retained: Rank 15000. Zero information loss.
- **[removed U+200B zero-width space from text columns] Rank 11595** - One text cell contained U+200B ZERO WIDTH SPACE inherited from the original Kaggle download (Name: Rank(s) [11595]). Only U+200B was removed; every other Unicode character was preserved. Confirmed 0 occurrences remain.
- **[converted Year to Int64] Rank all** - Whole-number check passed; missing count unchanged (269 -> 269); pd.NA preserved
- **[validated sales columns] Rank all** - no negatives, no missing, no text; zeros kept as genuine sales
- **[checked Genre/Platform/Publisher labels] Rank all** - no rewrites applied; findings: {'Genre': {'unique_values': 12, 'whitespace_issues': 0, 'case_variant_groups': []}, 'Platform': {'unique_values': 31, 'whitespace_issues': 0, 'case_variant_groups': []}, 'Publisher': {'unique_values': 578, 'whitespace_issues': 0, 'case_variant_groups': []}}

## 5. Known limitations

- **Four records dated 2017 / 2020 are retained** (Ranks 5959/2020, 14393/2017, 16244/2017, 16441/2017). Their Year values are exactly as provided by the source and have **not been independently verified**; they are documented as potential temporal inconsistencies. The dataset does **not** establish 2016 as a confirmed data coverage cutoff. Impact check (Stage A): excluding these four records changes none of the leading genre-platform combinations or regional rankings; their combined Global_Sales is 0.34M.
- **269 missing Year values are preserved** as missing (empty cells in the cleaned CSV; the raw file had 271, of which 2 belonged to a removed and a quarantined record). They must not become zero and rows are not deleted for it.
- **58 missing Publisher values** (57 after quarantine of Rank 4147) are preserved as missing; no category was invented for them.
- **Global_Sales was never recalculated.** Where Global_Sales differs from the sum of the four regions, the largest difference in the whole dataset is 0.02M, consistent with rounding (values reported to 2 decimals). No transformation was applied.
- **Zero sales are genuine sales information** (e.g. ~10.4k games never sold in Japan) and were kept as zeros, not treated as missing.
- **One invisible character was removed**: a U+200B zero-width space at the end of Rank 11595's Name, inherited from the original Kaggle dataset (see the record-level section above). The `remove_zero_width_spaces()` rule strips only U+200B from the text columns (Name, Platform, Genre, Publisher); no other Unicode character, whitespace or text was altered, and no other record contained it.
- **CSV does not preserve pandas dtypes**: after saving, Year reads back as float64 with NaN. Restore it with `pd.read_csv("data/processed/vgsales_cleaned.csv", dtype={"Year": "Int64"})`.
- Row count: 16,598 raw -> 16,595 cleaned (2 duplicates removed, 1 quarantined).
