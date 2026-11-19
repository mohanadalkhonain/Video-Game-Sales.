import pandas as pd

RAW_CSV_PATH = "data/raw/vgsales.csv"
AUDIT_REPORT_PATH = "outputs/cleaning_reports/dataset_audit.md"

SALES_COLUMNS = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales"]
REQUIRED_COLUMNS = [
    "Rank", "Name", "Platform", "Year", "Genre", "Publisher",
    "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales",
]


def load_raw_csv():
    """Load data/raw/vgsales.csv, with a clear error if it is missing."""
    try:
        df = pd.read_csv(RAW_CSV_PATH)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Raw dataset not found at: {RAW_CSV_PATH}\n"
        )
    print("Raw dataset:", RAW_CSV_PATH)
    return df


def count_missing(series):
    """Return (count, percent) of missing values in a column."""
    total = len(series)
    count = int(series.isna().sum())
    percent = (count / total * 100) if total else 0.0
    return count, percent


def audit_dataset(df):
    """Run all audit checks; returns the findings as a plain dictionary."""
    findings = {}
    total_rows = len(df)

    # Structure
    findings["rows"] = total_rows
    findings["columns"] = list(df.columns)
    findings["dtypes"] = {col: str(df[col].dtype) for col in df.columns}

    # Missing values per column.
    findings["missing"] = {
        col: {"count": count, "percent": round(percent, 2)}
        for col in df.columns
        for (count, percent) in [count_missing(df[col])]
        if count > 0
    }
    findings["columns_with_no_missing"] = [
        col for col in df.columns if df[col].isna().sum() == 0
    ]

    # Exact duplicates (all columns equal).
    findings["exact_duplicate_rows"] = int(df.duplicated().sum())
    findings["rows_involved_in_exact_duplicates"] = int(df.duplicated(keep=False).sum())

    # Duplicate game + platform combinations (same game on different
    # platforms is legitimate).
    combo_dupes = df[df.duplicated(subset=["Name", "Platform"], keep=False)]
    findings["duplicate_name_platform_combinations"] = int(
        df.duplicated(subset=["Name", "Platform"]).sum()
    )
    findings["rows_involved_in_name_platform_duplicates"] = len(combo_dupes)
    findings["name_platform_duplicate_examples"] = (
        combo_dupes[["Rank", "Name", "Platform", "Year", "Genre", "Global_Sales"]]
        .sort_values(["Name", "Platform"])
        .head(10)
        .to_string(index=False)
    )

    # Categorical values and whitespace/case consistency.
    for col in ["Genre", "Platform", "Publisher"]:
        values = sorted(df[col].dropna().astype(str).unique())
        findings[f"unique_{col.lower()}_count"] = len(values)
        if col != "Publisher":
            findings[f"unique_{col.lower()}_values"] = values
        findings[f"_{col}_has_whitespace_only_issues"] = bool(
            (df[col].dropna().astype(str) != df[col].dropna().astype(str).str.strip()).any()
        )

    # Sales validity: negatives, text, numeric range.
    findings["sales_invalid"] = {}
    for col in SALES_COLUMNS:
        numeric = pd.to_numeric(df[col], errors="coerce")
        findings["sales_invalid"][col] = {
            "negative_values": int((numeric < 0).sum()),
            "non_numeric_text_values": int(df[col].notna().sum() - numeric.notna().sum()),
            "min": float(numeric.min()),
            "max": float(numeric.max()),
        }

    # Year health: missing values, range, whole numbers, impossible years.
    year_numeric = pd.to_numeric(df["Year"], errors="coerce")
    findings["year"] = {
        "missing_count": int(df["Year"].isna().sum()),
        "min": float(year_numeric.min()),
        "max": float(year_numeric.max()),
        "non_integer_values": int(((year_numeric.dropna() % 1) != 0).sum()),
    }
    findings["year"]["suspicious_after_2016"] = int((year_numeric > 2016).sum())
    findings["year"]["suspicious_rows"] = (
        df[year_numeric > 2016][["Rank", "Name", "Platform", "Year", "Genre", "Publisher"]]
        .head(10)
        .to_string(index=False)
    )

    # Global_Sales vs the sum of the four regions (allowing rounding).
    region_sum = df[SALES_COLUMNS[:-1]].sum(axis=1, numeric_only=True)
    difference = (df["Global_Sales"] - region_sum).abs()
    findings["global_vs_regions"] = {
        # 0.01 tolerance covers rounding at 2 decimals.
        "agrees_within_0.01": int((difference <= 0.01).sum()),
        "disagree_over_0.01": int((difference > 0.01).sum()),
        "agree_percent": round(float((difference <= 0.01).mean() * 100), 3),
        "max_difference": float(difference.max()),
        "worst_rows": df.loc[difference.sort_values(ascending=False).index[:5]][
            ["Rank", "Name", "Platform", "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales"]
        ].to_string(index=False),
    }

    # Extra observations relevant to the research questions.
    findings["name_count_unique"] = int(df["Name"].nunique())
    findings["games_on_multiple_platforms"] = int(df["Name"].duplicated().sum())
    findings["publisher_missing_examples"] = (
        df[df["Publisher"].isna()][["Rank", "Name", "Platform", "Year", "Genre", "Global_Sales"]]
        .to_string(index=False)
    )
    findings["missing_sales_rows_by_column"] = {
        col: int(df[col].isna().sum()) for col in SALES_COLUMNS
    }
    # Zeros are genuine sales, not missing data.
    findings["zero_sales_counts"] = {col: int((df[col] == 0).sum()) for col in SALES_COLUMNS}

    return findings


def save_audit_report(findings, csv_path):
    """Write the audit report as a Markdown file the team can read."""
    report_path = AUDIT_REPORT_PATH

    lines = []
    lines.append("# Dataset Audit Report - Video Game Sales (vgsales.csv)")
    lines.append("")
    lines.append(f"Source file: `{csv_path.split('/')[-1]}` (placed manually in `data/raw/` after downloading from Kaggle)")
    lines.append("")
    lines.append("## 1. Structure")
    lines.append(f"- Rows: **{findings['rows']}**")
    lines.append(f"- Columns: **{len(findings['columns'])}** -> `{', '.join(findings['columns'])}`")
    lines.append("- Types: " + ", ".join(f"`{k}`: {v}" for k, v in findings["dtypes"].items()))
    lines.append("")
    lines.append("## 2. Missing values (count, percent)")
    lines.append("| Column | Missing | Percent |")
    lines.append("|---|---|---|")
    for col in findings["columns"]:
        if col in findings["missing"]:
            entry = findings["missing"][col]
            lines.append(f"| {col} | {entry['count']} | {entry['percent']}% |")
        else:
            lines.append(f"| {col} | 0 | 0% |")
    lines.append("")
    lines.append("## 3. Duplicates")
    lines.append(f"- Exact duplicate rows (all 11 columns equal): **{findings['exact_duplicate_rows']}** (rows involved: {findings['rows_involved_in_exact_duplicates']})")
    lines.append(f"- Duplicate **Name + Platform** combinations: **{findings['duplicate_name_platform_combinations']}** (rows involved: {findings['rows_involved_in_name_platform_duplicates']})")
    lines.append("- Note: the same Name on *different* platforms is legitimate and is not counted here.")
    lines.append("")
    lines.append("**Example duplicate Name+Platform rows (first 10):**")
    lines.append("```")
    lines.append(findings["name_platform_duplicate_examples"])
    lines.append("```")
    lines.append("")
    lines.append("## 4. Categorical columns")
    lines.append(f"- Genre ({findings['unique_genre_count']} unique): `{findings['unique_genre_values']}`")
    lines.append(f"- Platform ({findings['unique_platform_count']} unique): `{findings['unique_platform_values']}`")
    lines.append(f"- Publisher: {findings['unique_publisher_count']} unique values")
    lines.append("")
    lines.append("## 5. Sales column validity")
    lines.append("| Column | Negative | Non-numeric text | Min | Max |")
    lines.append("|---|---|---|---|---|")
    for col in SALES_COLUMNS:
        entry = findings["sales_invalid"][col]
        lines.append(f"| {col} | {entry['negative_values']} | {entry['non_numeric_text_values']} | {entry['min']} | {entry['max']} |")
    lines.append("")
    lines.append(f"Zero values (genuine zero sales, NOT missing data): {findings['zero_sales_counts']}")
    lines.append(f"Missing values inside sales columns (count, NOT zeros): {findings['missing_sales_rows_by_column']}")
    lines.append("")
    lines.append("## 6. Year column")
    year = findings["year"]
    lines.append(f"- Missing: **{year['missing_count']}**")
    lines.append(f"- Range: {year['min']} to {year['max']}")
    lines.append(f"- Non-integer values: {year['non_integer_values']}")
    lines.append(f"- Values after 2016 (suspicious / impossible for this snapshot): {year['suspicious_after_2016']}")
    if year["suspicious_after_2016"]:
        lines.append("```")
        lines.append(year["suspicious_rows"])
        lines.append("```")
    lines.append("")
    lines.append("## 7. Global_Sales vs sum of regions")
    gv = findings["global_vs_regions"]
    lines.append(f"- Agree within 0.01: {gv['agrees_within_0.01']} of {findings['rows']} ({gv['agree_percent']}%)")
    lines.append(f"- Disagree by more than 0.01: **{gv['disagree_over_0.01']}**")
    lines.append(f"- Largest discrepancy: {gv['max_difference']}")
    lines.append("Worst rows:")
    lines.append("```")
    lines.append(gv["worst_rows"])
    lines.append("```")
    lines.append("")
    lines.append("## 8. Extra observations")
    lines.append(f"- Unique game titles: {findings['name_count_unique']}")
    lines.append(f"- Rows whose title appears on more than one platform (legitimate): {findings['games_on_multiple_platforms']}")
    lines.append("")
    lines.append("Rows with a missing Publisher:")
    lines.append("```")
    lines.append(findings.get("publisher_missing_examples", "(none)"))
    lines.append("```")
    lines.append("")

    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write("\n".join(lines))
    print("Audit report written to:", report_path)
    return report_path


def main():
    df = load_raw_csv()
    if any(col not in df.columns for col in REQUIRED_COLUMNS):
        raise ValueError("The raw CSV is missing required columns; expected " + str(REQUIRED_COLUMNS))
    print("Loaded", len(df), "rows for audit.")
    print()

    findings = audit_dataset(df)
    report_path = save_audit_report(findings, RAW_CSV_PATH)

    print()
    print("=== AUDIT SUMMARY ===")
    print("Rows x Columns:", findings["rows"], "x", len(findings["columns"]))
    print("Missing values:", {k: v["count"] for k, v in findings["missing"].items()})
    print("Exact duplicate rows:", findings["exact_duplicate_rows"])
    print("Duplicate Name+Platform combos:", findings["duplicate_name_platform_combinations"])
    print("Sales negatives:", {k: v["negative_values"] for k, v in findings["sales_invalid"].items()})
    print("Year missing / >2016:", findings["year"]["missing_count"], "/", findings["year"]["suspicious_after_2016"])
    print("Global vs region sum disagreements (>0.01):", findings["global_vs_regions"]["disagree_over_0.01"])
    print()
    print("Full report:", report_path)


if __name__ == "__main__":
    main()
