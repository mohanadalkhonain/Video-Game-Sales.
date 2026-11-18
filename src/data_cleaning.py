import os

import pandas as pd

# Data cleaning constants 
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "vgsales.csv")
CLEANED_DATA_PATH = os.path.join(
    PROJECT_ROOT, "data", "processed", "vgsales_cleaned.csv"
)
REPORTS_DIR = os.path.join(PROJECT_ROOT, "outputs", "cleaning_reports")
REVIEW_FILE_PATH = os.path.join(REPORTS_DIR, "records_requiring_review.csv")
CLEANING_REPORT_PATH = os.path.join(REPORTS_DIR, "cleaning_report.md")

REQUIRED_COLUMNS = [
    "Rank", "Name", "Platform", "Year", "Genre", "Publisher",
    "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales",
]

SALES_COLUMNS = [
    "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales",
]

# Rank -> reason, quoted verbatim in the cleaning report.
RANKS_TO_REMOVE = {
    16130: (
        "Madden NFL 13 (PS3): duplicate game+platform record with conflicting "
        "sales figures (NOT an exact duplicate). A self-consistent partial "
        "tracking entry (Global 0.01M, all regions ~0) separate from the "
        "complete record at Rank 604. Kept: Rank 604. Sales effect of removal "
        "is calculated from the original CSV in the cleaning report."
    ),
    15002: (
        "Wii de Asobu: Metroid Prime (Wii): exact duplicate of Rank 15000 - "
        "all fields including every sales value are identical; only Rank "
        "differs. Retained: Rank 15000. Zero information loss."
    ),
}

RANKS_TO_QUARANTINE = {
    4147: (
        "Sonic the Hedgehog (PS3): conflicting sales figures versus retained "
        "Rank 1717 (EU_Sales 0.48 vs 0.07 - two records cannot both be right "
        "about the same quantity), and incomplete metadata (missing Year AND "
        "Publisher). Kept as a full record for review here; NOT deleted. "
        "Retained record: Rank 1717."
    ),
}


def load_data(path=RAW_DATA_PATH):
    """Load the raw dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Raw dataset not found at: {path}\n"
            
        )

    df = pd.read_csv(path)

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"The dataset is missing required columns: {missing_columns}. "
            f"Expected columns: {REQUIRED_COLUMNS}"
        )

    return df


def inspect_data(df):
    """Return shape, dtype, missing, duplicate and sales-column statistics.

    Used for the before and after snapshots, so report numbers are always
    computed the same way.
    """
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": {column: str(df[column].dtype) for column in df.columns},
        "missing_counts": {
            column: int(df[column].isna().sum()) for column in df.columns
        },
        "exact_duplicate_rows": int(df.duplicated().sum()),
        "duplicate_name_platform_combinations": int(
            df.duplicated(subset=["Name", "Platform"]).sum()
        ),
        "rows_involved_in_name_platform_duplicates": int(
            df.duplicated(subset=["Name", "Platform"], keep=False).sum()
        ),
        "sales_column_min": {
            column: float(df[column].min()) for column in SALES_COLUMNS
        },
        "sales_column_missing": {
            column: int(df[column].isna().sum()) for column in SALES_COLUMNS
        },
        "sales_column_negative": {
            column: int((df[column] < 0).sum()) for column in SALES_COLUMNS
        },
    }


def verify_rank_uniqueness(df):
    """Raise if Rank is not unique; the cleaning decisions identify records by Rank."""
    duplicate_ranks = df["Rank"][df["Rank"].duplicated()].tolist()
    if duplicate_ranks:
        raise ValueError(
            f"Cannot clean safely: Rank values are not unique. "
            f"Duplicated Ranks: {duplicate_ranks[:10]}"
        )


def quarantine_records(df):
 
    review_mask = df["Rank"].isin(RANKS_TO_QUARANTINE)
    review_records = df[review_mask].copy()
    remaining = df[~review_mask].copy()

    found_ranks = review_records["Rank"].tolist()
    for expected_rank in RANKS_TO_QUARANTINE:
        if expected_rank not in found_ranks:
            raise ValueError(
                f"Record to quarantine ({expected_rank}) was not found in "
                "the dataset - the cleaning decisions no longer match the "
                "raw file. STOP rather than clean a file we do not recognise."
            )
    return remaining, review_records


def remove_duplicate_records(df):
    """Remove the approved duplicate records, verifying each exists first."""
    keep_mask = ~df["Rank"].isin(RANKS_TO_REMOVE)
    for rank in RANKS_TO_REMOVE:
        if not (df["Rank"] == rank).any():
            raise ValueError(
                f"Record to remove ({rank}) was not found in the dataset - "
                "the cleaning decisions no longer match the raw file."
            )
    return df[keep_mask].copy()


def convert_year_to_integer(df):
    """Convert Year float64 -> nullable Int64, keeping missing values as NA.

    Refuses to convert if any non-missing Year is not a whole number;
    never rounds.
    """
    year_float = df["Year"].astype(float)
    non_missing_years = year_float.dropna()

    not_whole_numbers = non_missing_years[non_missing_years % 1 != 0]
    if len(not_whole_numbers) > 0:
        raise ValueError(
            f"Year contains non-whole-number values, refusing to convert "
            f"(no rounding allowed). Examples: {not_whole_numbers.head().tolist()}"
        )

    year_before_missing = int(df["Year"].isna().sum())
    df = df.copy()
    df["Year"] = df["Year"].astype("Int64")
    year_after_missing = int(df["Year"].isna().sum())

    if year_before_missing != year_after_missing:
        raise AssertionError(
            f"Year conversion changed the missing count: "
            f"{year_before_missing} -> {year_after_missing}"
        )

    return df, year_before_missing, year_after_missing


def validate_sales_columns(df):
    """Raise unless every sales column is numeric, non-negative and complete."""
    problems = []
    for column in SALES_COLUMNS:
        as_numeric = pd.to_numeric(df[column], errors="coerce")
        text_values = int(df[column].notna().sum() - as_numeric.notna().sum())
        negative_values = int((as_numeric < 0).sum())
        missing_values = int(df[column].isna().sum())

        if text_values:
            problems.append(f"{column}: {text_values} non-numeric text values")
        if negative_values:
            problems.append(f"{column}: {negative_values} negative values")
        if missing_values:
            problems.append(f"{column}: {missing_values} missing values")

    if problems:
        raise ValueError("Sales columns failed validation: " + "; ".join(problems))


def check_categorical_labels(df):
    """Report whitespace and case-variant issues in Genre/Platform/Publisher.

    Labels are only reported, never rewritten.
    """
    findings = {}
    for column in ["Genre", "Platform", "Publisher"]:
        values = df[column].dropna().astype(str)
        whitespace_issues = int((values != values.str.strip()).sum())

        grouped = values.groupby(values.str.casefold()).unique()
        case_variant_names = [
            group for group in grouped if len(group) > 1
        ]

        findings[column] = {
            "unique_values": int(values.nunique()),
            "whitespace_issues": whitespace_issues,
            "case_variant_groups": case_variant_names,
        }
    return findings


def clean_data(df):
    """Apply the approved cleaning decisions in order; returns
    (cleaned_df, review_records, action_log)."""
    verify_rank_uniqueness(df)
    action_log = []

    remaining_df, review_records = quarantine_records(df)
    for rank, reason in RANKS_TO_QUARANTINE.items():
        action_log.append({"rank": rank, "action": "quarantined", "reason": reason})

    cleaned_df = remove_duplicate_records(remaining_df)
    for rank, reason in RANKS_TO_REMOVE.items():
        action_log.append({"rank": rank, "action": "removed", "reason": reason})

    cleaned_df, year_missing_before, year_missing_after = convert_year_to_integer(cleaned_df)
    action_log.append({
        "rank": "all",
        "action": "converted Year to Int64",
        "reason": (
            f"Whole-number check passed; missing count unchanged "
            f"({year_missing_before} -> {year_missing_after}); pd.NA preserved"
        ),
    })

    validate_sales_columns(cleaned_df)
    action_log.append({
        "rank": "all",
        "action": "validated sales columns",
        "reason": "no negatives, no missing, no text; zeros kept as genuine sales",
    })

    categorical_findings = check_categorical_labels(cleaned_df)
    action_log.append({
        "rank": "all",
        "action": "checked Genre/Platform/Publisher labels",
        "reason": f"no rewrites applied; findings: {categorical_findings}",
    })

    return cleaned_df, review_records, action_log


def save_cleaned_data(df, path=CLEANED_DATA_PATH):
    """Save the cleaned dataset under data/processed/ (never the raw file).

    Missing years export as empty cells because CSV does not carry dtypes.
    """
    if os.path.abspath(path) == os.path.abspath(RAW_DATA_PATH):
        raise ValueError("Refusing to overwrite the raw dataset.")
    # Include the separator so sibling folders are not accepted by the prefix.
    processed_dir = os.path.join(PROJECT_ROOT, "data", "processed") + os.sep
    if not os.path.abspath(path).startswith(processed_dir):
        raise ValueError("Cleaned data must be saved under data/processed/.")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Cleaned dataset written to: {path} ({len(df)} rows)")
    return path


def save_review_records(review_records, path=REVIEW_FILE_PATH):
    """Save quarantined records to outputs/cleaning_reports/ for review."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    review_records.to_csv(path, index=False)
    print(f"Review records written to: {path} ({len(review_records)} rows)")
    return path


def compare_stats(before_stats, after_stats):
    """Build the before/after comparison table for the cleaning report."""
    comparison = {
        "rows": {"before": before_stats["rows"], "after": after_stats["rows"]},
        "exact_duplicate_rows": {
            "before": before_stats["exact_duplicate_rows"],
            "after": after_stats["exact_duplicate_rows"],
        },
        "duplicate_name_platform_combinations": {
            "before": before_stats["duplicate_name_platform_combinations"],
            "after": after_stats["duplicate_name_platform_combinations"],
        },
        "missing_values": {},
        "year_dtype": {
            "before": before_stats["dtypes"]["Year"],
            "after": after_stats["dtypes"]["Year"],
        },
    }
    for column in before_stats["columns"]:
        comparison["missing_values"][column] = {
            "before": before_stats["missing_counts"][column],
            "after": after_stats["missing_counts"].get(column, 0),
        }
    return comparison


def sales_reconciliation(original_df, cleaned_df, review_df, removed_rows):
    """Verify raw totals = cleaned + quarantined + removed, per sales column.

    A zero difference proves no sales value was created, modified or lost.
    """
    reconciliation = {}
    quarantined_sales = review_df[SALES_COLUMNS].sum()
    removed_sales = removed_rows[SALES_COLUMNS].sum()

    for column in SALES_COLUMNS:
        raw_total = float(original_df[column].sum())
        cleaned_total = float(cleaned_df[column].sum())
        quarantined_total = float(quarantined_sales[column])
        explained = float(
            cleaned_total
            + quarantined_total
            + removed_sales[column]
        )
        reconciliation[column] = {
            "raw_total": round(raw_total, 6),
            "cleaned_total": round(cleaned_total, 6),
            "quarantined": round(quarantined_total, 6),
            "removed": round(float(removed_sales[column]), 6),
            "difference": round(raw_total - explained, 6),
        }
    return reconciliation


def write_cleaning_report(
    before_stats,
    after_stats,
    action_log,
    original_df,
    removed_rows,
    review_df,
    reconciliation,
    original_row_count,
    report_path=CLEANING_REPORT_PATH,
):
    """Write the Markdown cleaning report: before/after statistics, a
    record-level explanation of every affected row, reconciliation and
    limitations."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    comparison = compare_stats(before_stats, after_stats)

    lines = []
    lines.append("# Cleaning Report - Video Game Sales (Member 1)")
    lines.append("")
    lines.append("Source: `data/raw/vgsales.csv` (original download, unmodified).")
    lines.append(f"Outputs: `data/processed/vgsales_cleaned.csv`, `{os.path.basename(REVIEW_FILE_PATH)}`.")
    lines.append("")
    lines.append("## 1. Before / after summary")
    lines.append("")
    lines.append("| Metric | Before (raw) | After (cleaned) |")
    lines.append("|---|---|---|")
    lines.append(f"| Row count | {comparison['rows']['before']} | {comparison['rows']['after']} |")
    lines.append(f"| Exact duplicate rows | {comparison['exact_duplicate_rows']['before']} | {comparison['exact_duplicate_rows']['after']} |")
    lines.append(
        f"| Duplicate Name+Platform combinations | {comparison['duplicate_name_platform_combinations']['before']} "
        f"| {comparison['duplicate_name_platform_combinations']['after']} "
        f"(remaining pairs are different-year releases of the same title: legitimate) |"
    )
    lines.append(f"| Year column type | {comparison['year_dtype']['before']} | `{comparison['year_dtype']['after']}` |")
    lines.append("")
    lines.append("### Missing values before vs after")
    lines.append("")
    lines.append("| Column | Before | After | Why it moved |")
    lines.append("|---|---|---|---|")
    why_move = {
        "Year": "quarantined Rank 4147 (missing Year) and removed Rank 15002 (missing Year)",
        "Publisher": "quarantined Rank 4147 (missing Publisher)",
    }
    for column, values in comparison["missing_values"].items():
        moved = values["before"] != values["after"]
        note = why_move.get(column, "-") if moved else "unchanged"
        lines.append(f"| {column} | {values['before']} | {values['after']} | {note} |")
    lines.append("")
    lines.append("## 2. Record-level explanation of every affected row")
    lines.append("")
    lines.append("Every removed or quarantined row is shown exactly as it appeared in the "
                 "original data. Row numbers are pandas positional indices, where 0 is the "
                 "first data row; the equivalent 1-based CSV line (including the header) is "
                 "index + 2.")
    lines.append("")
    removed_ranks = removed_rows["Rank"].tolist()
    for rank in removed_ranks:
        record_sales = removed_rows[removed_rows["Rank"] == rank]
        effect_text = ", ".join(
            f"{column} {float(record_sales[column].sum()):.2f}M"
            for column in SALES_COLUMNS
        )
        lines.append(f"### Removed - Rank {rank}")
        lines.append(f"- **Reason:** {RANKS_TO_REMOVE[rank]}")
        lines.append(
            f"- **Actual effect on sales totals, summed directly from the "
            f"original CSV:** {effect_text}."
        )
        row = record_sales.iloc[0]
        raw_index = int(original_df.index[original_df["Rank"] == rank][0])
        lines.append("- Row as it appeared in the raw data (pandas row index "
                     f"{raw_index}; CSV line {raw_index + 2} with the header included):")
        lines.append("```")
        lines.append(row.to_string())
        lines.append("```")
        lines.append("")
    for _, row in review_df.iterrows():
        lines.append(f"### Quarantined (NOT deleted) - Rank {int(row['Rank'])}")
        lines.append(f"- **Reason:** {RANKS_TO_QUARANTINE[int(row['Rank'])]}")
        lines.append("- **Potential effect on regional totals if ever re-added:** "
                     "adds NA 0.00M, EU 0.48M, JP 0.00M, Other 0.00M, Global 0.48M "
                     "(EU total would rise by 0.48M and the Action/PS3 EU combination "
                     "would gain 0.48M - it is kept out of the primary dataset until "
                     "reviewed because its EU figure contradicts Rank 1717's 0.07M).")
        raw_index = int(original_df.index[original_df["Rank"] == int(row["Rank"])][0])
        lines.append("- Row as it appeared in the raw data (pandas row index "
                     f"{raw_index}; CSV line {raw_index + 2} with the header included):")
        lines.append("```")
        lines.append(row.to_string())
        lines.append("```")
        lines.append("")
    lines.append("## 3. Sales reconciliation (before vs after)")
    lines.append("")
    lines.append("Check: raw total = cleaned total + quarantined + removed. A difference of 0.00 proves no sales value was created, modified or lost during cleaning.")
    lines.append("")
    lines.append("| Column | Raw total | Cleaned total | Quarantined | Removed | Difference |")
    lines.append("|---|---|---|---|---|---|")
    for column, values in reconciliation.items():
        lines.append(
            f"| {column} | {values['raw_total']:.2f} | {values['cleaned_total']:.2f} "
            f"| {values['quarantined']:.2f} | {values['removed']:.2f} "
            f"| {values['difference']:.2f} |"
        )
    lines.append("")
    lines.append("## 4. Actions applied (in order)")
    lines.append("")
    for entry in action_log:
        lines.append(f"- **[{entry['action']}] Rank {entry['rank']}** - {entry['reason']}")
    lines.append("")
    lines.append("## 5. Known limitations passed to Members 2 and 3")
    lines.append("")
    lines.append("- **Four records dated 2017 / 2020 are retained** (Ranks 5959/2020, 14393/2017, "
                 "16244/2017, 16441/2017). Their Year values are exactly as provided by the "
                 "source and have **not been independently verified**; they are documented as "
                 "potential temporal inconsistencies. The dataset does **not** establish 2016 "
                 "as a confirmed data coverage cutoff. Impact check (Stage A): excluding these "
                 "four records changes none of the leading genre-platform combinations or "
                 "regional rankings; their combined Global_Sales is 0.34M.")
    lines.append("- **269 missing Year values are preserved** as missing (empty cells in the "
                 "cleaned CSV; the raw file had 271, of which 2 belonged to a removed and a "
                 "quarantined record). They must not become zero and rows are not deleted for it.")
    lines.append("- **58 missing Publisher values** (57 after quarantine of Rank 4147) are "
                 "preserved as missing; no category was invented for them.")
    lines.append("- **Global_Sales was never recalculated.** Where Global_Sales differs from the "
                 "sum of the four regions, the largest difference in the whole dataset is 0.02M, "
                 "consistent with rounding (values reported to 2 decimals). No transformation was applied.")
    lines.append("- **Zero sales are genuine sales information** (e.g. ~10.4k games never sold in "
                 "Japan) and were kept as zeros, not treated as missing.")
    lines.append("- **CSV does not preserve pandas dtypes**: after saving, Year reads back as "
                 "float64 with NaN. Restore it with "
                 "`pd.read_csv(\"data/processed/vgsales_cleaned.csv\", dtype={\"Year\": \"Int64\"})`.")
    lines.append("- Row count: 16,598 raw -> 16,595 cleaned (2 duplicates removed, 1 quarantined).")
    lines.append("")

    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write("\n".join(lines))
    print(f"Cleaning report written to: {report_path}")
    return report_path


def validate_outputs(original_df, cleaned_df, review_df):
    """Run the 10-point validation checklist; returns (passed, reconciliation, checks)."""
    checks = []

    def record_check(description, passed, detail=""):
        checks.append((description, passed, detail))
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {description}" + (f" - {detail}" if detail else ""))

    print("\n=== VALIDATION CHECKLIST ===")

    record_check(
        "Original raw dataset still has 16,598 rows",
        len(original_df) == 16598,
        f"found {len(original_df)}"
    )

    ranks_gone = all((original_df["Rank"] == r).any() and
                     not (cleaned_df["Rank"] == r).any()
                     for r in RANKS_TO_REMOVE)
    record_check(
        f"Exactly the two approved duplicates (Ranks {sorted(RANKS_TO_REMOVE)}) removed",
        ranks_gone and set(RANKS_TO_REMOVE) == {16130, 15002}
    )

    record_check(
        "Exactly one record quarantined (Sonic Rank 4147)",
        len(review_df) == 1 and int(review_df.iloc[0]["Rank"]) == 4147,
        f"review file holds Ranks {review_df['Rank'].tolist()}"
    )

    record_check(
        "Cleaned dataset has 16,595 rows (16,598 - 2 removed - 1 quarantined)",
        len(cleaned_df) == 16595,
        f"found {len(cleaned_df)}"
    )

    expected_review_values = original_df.loc[original_df["Rank"] == 4147].iloc[0]
    actual_review_values = review_df.iloc[0]
    unchanged = all(
        (pd.isna(expected) and pd.isna(actual)) or (expected == actual)
        for expected, actual in zip(expected_review_values, actual_review_values)
    )
    record_check(
        "Review file holds Rank 4147 exactly as it appeared in the raw data",
        unchanged
    )

    record_check(
        "All 11 original columns preserved in cleaned data",
        list(cleaned_df.columns) == list(original_df.columns),
        ", ".join(cleaned_df.columns)
    )

    year_missing_cleaned = int(cleaned_df["Year"].isna().sum())
    year_missing_raw = int(original_df["Year"].isna().sum())
    record_check(
        "Missing Year values remain missing (none filled)",
        year_missing_cleaned == year_missing_raw - 2,
        f"{year_missing_raw} raw - 2 (Ranks 15002 and 4147) = {year_missing_cleaned} expected"
    )

    future_years = cleaned_df[cleaned_df["Year"] > 2016]
    record_check(
        "All four 2017/2020 records retained, Year values unmodified",
        len(future_years) == 4
        and sorted(future_years["Year"].tolist()) == [2017, 2017, 2017, 2020],
        f"Ranks {future_years['Rank'].tolist()}"
    )

    removed_rows = original_df[original_df["Rank"].isin(RANKS_TO_REMOVE)]
    reconciliation = sales_reconciliation(original_df, cleaned_df, review_df, removed_rows)
    balanced = all(abs(v["difference"]) < 1e-9 for v in reconciliation.values())
    record_check(
        "Sales totals reconcile exactly (raw = cleaned + quarantined + removed)",
        balanced,
        "; ".join(f"{c}: diff {v['difference']:.4f}" for c, v in reconciliation.items()),
    )

    expected_surviving = set(original_df["Rank"]) - set(RANKS_TO_REMOVE) - {4147}
    actual_surviving = set(cleaned_df["Rank"])
    record_check(
        "Only the three decided records differ from the raw data",
        expected_surviving == actual_surviving,
        f"{len(actual_surviving)} surviving records"
    )

    failures = [c for c in checks if not c[1]]
    return not failures, reconciliation, checks


def dataframes_match(left_df, right_df):
    """Compare two DataFrames cell by cell; missing values count as equal.

    Column-wise and dtype-tolerant, so a CSV round-trip counts as a match.
    """
    if len(left_df) != len(right_df):
        return False
    if list(left_df.columns) != list(right_df.columns):
        return False

    for column in left_df.columns:
        left_column = left_df[column].reset_index(drop=True)
        right_column = right_df[column].reset_index(drop=True)

        if not pd.isna(left_column).equals(pd.isna(right_column)):
            return False
        both_present = left_column.notna() & right_column.notna()
        equal_values = (
            left_column[both_present].reset_index(drop=True)
            == right_column[both_present].reset_index(drop=True)
        )
        if not bool(equal_values.all()):
            return False
    return True


def verify_saved_output_files(
    cleaned_df, review_records, original_df,
    staged_cleaned_path, staged_review_path, staged_report_path,
):
    """Reload the staged files and verify their actual contents before publishing.

    Checks row count, column order, Rank values, all sales values, the
    missing-Year pattern, the Int64 load path, report completeness, and the
    staged review CSV against both the in-memory record and the raw record.
    """
    staged_paths = [staged_cleaned_path, staged_review_path, staged_report_path]
    for path in staged_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Staged output file was not written: {path}")
        if os.path.getsize(path) == 0:
            raise ValueError(f"Staged output file is empty (incomplete): {path}")

    problems = []

    try:
        reloaded_cleaned = pd.read_csv(staged_cleaned_path, dtype={"Year": "Int64"})

        if len(reloaded_cleaned) != len(cleaned_df):
            problems.append(
                f"staged cleaned CSV has {len(reloaded_cleaned)} rows, "
                f"intended {len(cleaned_df)}"
            )
        if int(reloaded_cleaned["Year"].isna().sum()) != 269:
            problems.append(
                f"staged cleaned CSV has {int(reloaded_cleaned['Year'].isna().sum())} "
                "missing Year values; the approved decisions produce 269"
            )
        if list(map(int, reloaded_cleaned["Rank"])) != list(map(int, cleaned_df["Rank"])):
            problems.append("staged cleaned CSV Rank values differ from the intended cleaned data")
        reloaded_sales = {
            column: [float(value) for value in reloaded_cleaned[column]]
            for column in SALES_COLUMNS
        }
        intended_sales = {
            column: [float(value) for value in cleaned_df[column]]
            for column in SALES_COLUMNS
        }
        for column in SALES_COLUMNS:
            if reloaded_sales[column] != intended_sales[column]:
                problems.append(f"staged cleaned CSV sales values differ in {column}")
        if not dataframes_match(reloaded_cleaned, cleaned_df):
            problems.append("staged cleaned CSV does not reproduce the cleaned data in memory")
    except Exception as section_error:
        raise ValueError(
            f"staged cleaned CSV ({staged_cleaned_path}) is not a valid "
            f"cleaned dataset: {section_error}"
        ) from section_error

    try:
        reloaded_review = pd.read_csv(staged_review_path)
        if not dataframes_match(reloaded_review, review_records):
            problems.append("staged review CSV does not reproduce the quarantined records in memory")
        raw_quarantined = original_df[original_df["Rank"].isin(RANKS_TO_QUARANTINE)]
        if not dataframes_match(reloaded_review, raw_quarantined):
            problems.append("staged review CSV does not match the original raw quarantined record")
    except Exception as section_error:
        raise ValueError(
            f"staged review CSV ({staged_review_path}) is not a valid "
            f"review file: {section_error}"
        ) from section_error

    if problems:
        raise ValueError("; ".join(problems))

    print(
        f"Staged cleaned CSV verified: {len(reloaded_cleaned)} rows x "
        f"{len(reloaded_cleaned.columns)} columns (column order intact), "
        f"Rank values match, all 5 sales columns match, "
        f"missing Year = {int(reloaded_cleaned['Year'].isna().sum())}, "
        f"Int64 load successful"
    )
    print(
        f"Staged review CSV verified: every field matches the in-memory record "
        f"and the original raw record (Rank(s) {reloaded_review['Rank'].tolist()})"
    )


def publish_pending_outputs(pending_and_final_paths):
    """Publish staged files onto final names with backup-and-rollback.

    Each existing final file is moved to a .previous backup before the
    staged file takes its place; if any rename fails, published files are
    removed and backups restored, so outputs end fully updated or exactly
    as before. Backups are deleted after a successful publish.
    """
    backups = []
    published = []
    try:
        for pending_path, final_path in pending_and_final_paths:
            backup_path = final_path + ".previous"
            if os.path.exists(final_path):
                os.replace(final_path, backup_path)
                backups.append((backup_path, final_path))
            os.replace(pending_path, final_path)
            published.append(final_path)
            print(f"Published: {final_path}")
    except OSError:
        print("Publication failed part-way - rolling back to the previous outputs.")
        for final_path in published:
            if os.path.exists(final_path):
                os.remove(final_path)
        for backup_path, final_path in backups:
            os.replace(backup_path, final_path)
        print("Rollback complete: every final output is back to its previous state.")
        raise
    for backup_path, _ in backups:
        if os.path.exists(backup_path):
            os.remove(backup_path)


def discard_pending_outputs(pending_paths):
    """Delete staging files that were never published (after a failed run)."""
    for path in pending_paths:
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed unpublished staging file: {path}")
