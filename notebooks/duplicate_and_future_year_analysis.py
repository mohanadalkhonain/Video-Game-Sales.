"""

Part 1: column-by-column comparison of the three suspected duplicate groups.
Part 2: impact of the four records dated 2017/2020 on the leading
genre/platform results per region.

Run from the project root:  py notebooks/duplicate_and_future_year_analysis.py
"""

import pandas as pd

RAW_CSV = "data/raw/vgsales.csv"
SALES_COLUMNS = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales"]
REGION_COLUMNS = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]

GROUPS = [
    ("Madden NFL 13", "PS3"),
    ("Sonic the Hedgehog", "PS3"),
    ("Wii de Asobu: Metroid Prime", "Wii"),
]

ALL_COLS = [
    "Rank", "Name", "Platform", "Year", "Genre", "Publisher",
    "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales",
]

df = pd.read_csv(RAW_CSV)

print("=" * 70)
print("PART 1 - DUPLICATE GROUP COMPARISON")
print("=" * 70)

for name, platform in GROUPS:
    group = df[(df["Name"] == name) & (df["Platform"] == platform)]
    print()
    print(f"### {name} ({platform}) - {len(group)} rows")
    print(group.to_string())
    print()

    # Columns that differ, and which of them are real conflicts.
    row_a, row_b = group.iloc[0], group.iloc[1]
    differ = []
    conflicts = []
    for col in ALL_COLS:
        value_a, value_b = row_a[col], row_b[col]
        both_known = not (pd.isna(value_a) or pd.isna(value_b))
        if both_known and value_a != value_b:
            differ.append(f"{col} (a={value_a} vs b={value_b})")
            conflicts.append(col)
        elif not both_known and str(value_a) != str(value_b):
            differ.append(f"{col} (a={value_a} vs b={value_b}); one side missing")

    if not conflicts and not differ:
        print("Result: the two rows are IDENTICAL apart from their Rank.")
    else:
        print("Columns where the rows differ:")
        for line in differ:
            print("  -", line)
        print("Descriptive fields (Year/Genre/Publisher) conflict:", bool(
            [c for c in conflicts if c in ("Year", "Genre", "Publisher")]
        ))
        print("Sales-value differences:", [c for c in conflicts if c in SALES_COLUMNS] or "none")

print()
print("=" * 70)
print("PART 2 - IMPACT OF THE FOUR 2017/2020 RECORDS")
print("=" * 70)

future_rows = df[df["Year"] > 2016]
print()
print("The four records:")
print(future_rows.to_string(index=False))
print()
print("Combined sales of the four records (millions):")
for col in SALES_COLUMNS:
    print(f"  {col}: {future_rows[col].sum():.2f}  ({future_rows[col].tolist()})")
print()


def leading_results(data):
    """Leading genre x platform combo per region + genre totals and averages."""
    results = {}
    for region in SALES_COLUMNS:
        results[region] = data.groupby(["Genre", "Platform"])[region].sum().sort_values(ascending=False).head(5)
    results["genre_total_global"] = data.groupby("Genre")["Global_Sales"].sum().sort_values(ascending=False)
    results["genre_avg_global"] = data.groupby("Genre")["Global_Sales"].mean().sort_values(ascending=False)
    return results


with_future = leading_results(df)
# Exclude ONLY the four future-dated rows, keeping the NaN-year rows.
without_future = leading_results(df.drop(index=future_rows.index))

print("Top-5 Genre+Platform combos per region, WITH vs WITHOUT the 4 records:")
for region in SALES_COLUMNS:
    label = f"{region} (Global_Sales uses genre x platform too)"
    if region == "Global_Sales":
        label = "Global_Sales"
    print()
    print(f"--- {label} ---")
    comparison = pd.DataFrame({
        "with 4 records": with_future[region].head(3),
        "without 4 records": without_future[region].head(3),
    })
    print(comparison.to_string())
    top_with = with_future[region].head(3).index.tolist()
    top_without = without_future[region].head(3).index.tolist()
    print("Top-3 unchanged:", top_with == top_without)

print()
print("Genre ranking by TOTAL Global_Sales:")
ranks_with = with_future["genre_total_global"].head(5)
ranks_without = without_future["genre_total_global"].head(5)
print(pd.DataFrame({
    "with 4 records": {str(k): round(v, 2) for k, v in ranks_with.items()},
    "without 4 records": {str(k): round(v, 2) for k, v in ranks_without.items()},
}).to_string())

print()
print("Genre ranking by AVERAGE Global_Sales per release:")
avg_with = with_future["genre_avg_global"].head(5)
avg_without = without_future["genre_avg_global"].head(5)
print(pd.DataFrame({
    "with 4 records": {str(k): round(v, 4) for k, v in avg_with.items()},
    "without 4 records": {str(k): round(v, 4) for k, v in avg_without.items()},
}).to_string())
