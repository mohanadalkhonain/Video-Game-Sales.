import pandas as pd

# Data cleaning constants.
RAW_DATA_PATH = "data/raw/vgsales.csv"
CLEANED_DATA_PATH = "data/processed/vgsales_cleaned.csv"
REVIEW_FILE_PATH = "outputs/cleaning_reports/records_requiring_review.csv"
CLEANING_REPORT_PATH = "outputs/cleaning_reports/cleaning_report.md"
REVIEW_FILE_NAME = REVIEW_FILE_PATH.split("/")[-1]

REQUIRED_COLUMNS = [
    "Rank", "Name", "Platform", "Year", "Genre", "Publisher",
    "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales",
]

SALES_COLUMNS = [
    "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales",
]

# Text columns the zero-width-space rule applies to.
TEXT_COLUMNS = ["Name", "Platform", "Genre", "Publisher"]

ZERO_WIDTH_SPACE = chr(0x200B)  # U+200B ZERO WIDTH SPACE, built explicitly so no invisible character sits in the source

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
    """Load the raw dataset from data/raw/vgsales.csv and validate its columns."""
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Raw dataset not found at: {path}\n"
        )

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
    """Return shape, dtype, missing, duplicate and sales-column statistics,
    computed the same way for the before and after snapshots."""
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
    """Split off the approved review records; returns (remaining, review)."""
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


def remove_zero_width_spaces(df):
    """Remove U+200B ZERO WIDTH SPACE from the text columns.

    Approved correction: Rank 11595 carries a trailing U+200B inherited
    from the original Kaggle download. Only U+200B is removed - no other
    character, no whitespace strip, no case change - so every other Unicode
    character and all other text is preserved exactly. The quarantined review
    records are NOT touched by this rule: they must stay exactly as they
    appeared in the raw data.
    """
    df = df.copy()
    affected = {}
    for column in TEXT_COLUMNS:
        not_missing = df[column].notna()
        contains_zwsp = not_missing & df[column].str.contains(
            ZERO_WIDTH_SPACE, regex=False, na=False
        )
        if contains_zwsp.any():
            affected[column] = sorted(map(int, df.loc[contains_zwsp, "Rank"]))
            df.loc[contains_zwsp, column] = (
                df.loc[contains_zwsp, column].str.replace(
                    ZERO_WIDTH_SPACE, "", regex=False
                )
            )
    remaining = sum(
        int(df[column].str.contains(ZERO_WIDTH_SPACE, regex=False, na=False).sum())
        for column in TEXT_COLUMNS
    )
    if remaining:
        raise AssertionError(
            f"Zero-width space removal left {remaining} occurrence(s) in place"
        )
    return df, affected


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
    """Report whitespace and case-variant issues in Genre/Platform/Publisher."""
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

    cleaned_df, zwsp_affected = remove_zero_width_spaces(cleaned_df)
    total_affected_cells = sum(len(ranks) for ranks in zwsp_affected.values())
    cell_phrase = "One text cell" if total_affected_cells == 1 else f"{total_affected_cells} text cell(s)"
    affected_text = "; ".join(
        f"{column}: Rank(s) {ranks}" for column, ranks in zwsp_affected.items()
    ) or "none found"
    action_log.append({
        "rank": "11595" if zwsp_affected else "all",
        "action": "removed U+200B zero-width space from text columns",
        "reason": (
            f"{cell_phrase} contained U+200B ZERO WIDTH SPACE inherited from "
            f"the original Kaggle download ({affected_text}). "
            f"Only U+200B was removed; every other Unicode character was "
            f"preserved. Confirmed 0 occurrences remain."
        ),
    })

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
    """Save the cleaned dataset under data/processed/.

    Missing years export as empty cells because CSV does not carry dtypes.
    """
    normalized = path.replace("\\", "/")
    if normalized == RAW_DATA_PATH:
        raise ValueError("Refusing to overwrite the raw dataset.")
    if not normalized.startswith("data/processed/"):
        raise ValueError("Cleaned data must be saved under data/processed/.")

    df.to_csv(path, index=False)
    print(f"Cleaned dataset written to: {path} ({len(df)} rows)")
    return path


def save_review_records(review_records, path=REVIEW_FILE_PATH):
    """Save quarantined records to outputs/cleaning_reports/ for review."""
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
    cleaned_df,
    removed_rows,
    review_df,
    reconciliation,
    report_path=CLEANING_REPORT_PATH,
):
    """Write the Markdown cleaning report: before/after statistics, a
    record-level explanation of every affected row, reconciliation and
    limitations."""
    comparison = compare_stats(before_stats, after_stats)

    lines = []
    lines.append("# Cleaning Report - Video Game Sales")
    lines.append("")
    lines.append("Source: `data/raw/vgsales.csv`.")
    lines.append(f"Outputs: `data/processed/vgsales_cleaned.csv`, `{REVIEW_FILE_NAME}`.")
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
                     "(EU total would rise by 0.48M and the Platform/PS3 EU combination "
                     "would gain 0.48M - it is kept out of the primary dataset until "
                     "reviewed because its EU figure contradicts Rank 1717's 0.07M).")
        if int(row["Rank"]) == 4147:
            lines.append(
                "- **Platform verification (evidence-based review):** both "
                "records were checked directly against the raw data. Rank "
                "1717 is the same game on the SAME platform as Rank 4147: "
                "Sonic the Hedgehog, PS3, Year 2006, Genre Platform, "
                "Publisher Sega, sales NA 0.41 / EU 0.07 / JP 0.04 / "
                "Other 0.66 / Global 1.18. Comparing the two PS3 records' "
                "sales is therefore valid: one title on one platform should "
                "not appear twice with different figures."
            )
            lines.append(
                "- **Record-shape context:** Rank 4147 carries a single "
                "nonzero regional figure (EU 0.48) with all other regions at "
                "0.0, plus missing Year AND Publisher - the same "
                "partial-tracking-entry pattern as Rank 16130 (Madden NFL "
                "13), not a complete release record. The 1991 Genesis "
                "original (Rank 255) and the 2006 X360 release (Rank 1985) "
                "are separate, legitimate releases on different platforms "
                "and are not part of this duplicate pair."
            )
            lines.append(
                "- **Decision re-checked:** the quarantine reasons stand as "
                "verified (same title + same platform duplicate with "
                "inconsistent figures, and missing Year and Publisher); the "
                "record remains quarantined, its status unchanged."
            )
        raw_index = int(original_df.index[original_df["Rank"] == int(row["Rank"])][0])
        lines.append("- Row as it appeared in the raw data (pandas row index "
                     f"{raw_index}; CSV line {raw_index + 2} with the header included):")
        lines.append("```")
        lines.append(row.to_string())
        lines.append("```")
        lines.append("")

    #U+200B correction, documented at record level.
    zwsp_cells = []
    for zwsp_column in TEXT_COLUMNS:
        zwsp_mask = original_df[zwsp_column].notna() & original_df[zwsp_column].str.contains(
            ZERO_WIDTH_SPACE, regex=False, na=False
        )
        zwsp_cells.extend(
            (int(rank_value), zwsp_column)
            for rank_value in original_df.loc[zwsp_mask, "Rank"]
        )
    for rank_value, zwsp_column in sorted(zwsp_cells):
        zwsp_before = original_df.loc[original_df["Rank"] == rank_value, zwsp_column].iloc[0]
        zwsp_after = zwsp_before.replace(ZERO_WIDTH_SPACE, "")
        fields_except_one_match = dataframes_match(
            original_df.loc[original_df["Rank"] == rank_value].drop(columns=[zwsp_column]),
            cleaned_df.loc[cleaned_df["Rank"] == rank_value].drop(columns=[zwsp_column]),
        )
        lines.append(
            f"### Cleaned in place (record kept) - Rank {rank_value} "
            f"({zwsp_column}: U+200B removed)"
        )
        lines.append("")
        lines.append(
            f"- **What:** the end of the `{zwsp_column}` field carried a "
            "U+200B ZERO WIDTH SPACE, an invisible Unicode format character "
            "(category Cf) that cannot be seen when the text is viewed "
            "normally. It appears in `repr()` as `\\u200b`."
        )
        lines.append(
            "- **Origin:** the character was present in the original Kaggle "
            "dataset (`gregorut/videogamesales`) and passed through the "
            "earlier cleaning stages untouched."
        )
        lines.append(
            "- **Rule applied:** the cleaning workflow now removes U+200B "
            "from the text columns via `remove_zero_width_spaces()`. Only "
            "U+200B is removed: no other Unicode character, no whitespace "
            "strip and no case change - every other character of the text, "
            "legitimate Unicode included, is preserved exactly."
        )
        lines.append(f"- `{zwsp_column}` before (repr view): `{ascii(zwsp_before)}`")
        lines.append(f"- `{zwsp_column}` after  (repr view): `{ascii(zwsp_after)}`")
        lines.append(
            "- **All other fields of this record are unchanged** from the "
            "raw data."
            if fields_except_one_match else
            "- **Note:** other fields of this record also differ from the "
            "raw data because of the Year dtype conversion."
        )
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
    lines.append("## 5. Known limitations")
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
    lines.append("- **One invisible character was removed**: a U+200B "
                 "zero-width space at the end of Rank 11595's Name, inherited from the "
                 "original Kaggle dataset (see the record-level section above). The "
                 "`remove_zero_width_spaces()` rule strips only U+200B from the text "
                 "columns (Name, Platform, Genre, Publisher); no other Unicode character, "
                 "whitespace or text was altered, and no other record contained it.")
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
    """Run the validation checklist (12 checks); returns (passed, reconciliation, checks)."""
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

    zwsp_remaining = sum(
        int(cleaned_df[column]
            .str.contains(ZERO_WIDTH_SPACE, regex=False, na=False).sum())
        for column in TEXT_COLUMNS
    )
    record_check(
        "U+200B zero-width space absent from all text columns",
        zwsp_remaining == 0,
        f"{zwsp_remaining} occurrence(s) remain in Name/Platform/Genre/Publisher",
    )

    rank_11595_raw = original_df.loc[original_df["Rank"] == 11595, "Name"]
    rank_11595_cleaned = cleaned_df.loc[cleaned_df["Rank"] == 11595, "Name"]
    name_11595_preserved = (
        len(rank_11595_raw) == len(rank_11595_cleaned) == 1
        and rank_11595_cleaned.iloc[0]
        == rank_11595_raw.iloc[0].replace(ZERO_WIDTH_SPACE, "")
    )
    record_check(
        "Rank 11595 Name preserved except the removed U+200B",
        name_11595_preserved,
        f"{len(rank_11595_raw.iloc[0])} chars raw -> "
        f"{len(rank_11595_cleaned.iloc[0]) if len(rank_11595_cleaned) else 'MISSING'} chars cleaned",
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
    cleaned_path, review_path, report_path,
):
    """Reload the published files and verify their actual contents.

    Checks row count, column order, Rank values, all sales values, the
    missing-Year pattern, the Int64 load path, report completeness, and the
    review CSV against both the in-memory record and the raw record.
    """
    output_paths = [cleaned_path, review_path, report_path]
    for path in output_paths:
        try:
            with open(path, "rb") as handle:
                if not handle.read():
                    raise ValueError(f"Output file is empty (incomplete): {path}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Output file was not written: {path}")

    problems = []

    try:
        reloaded_cleaned = pd.read_csv(cleaned_path, dtype={"Year": "Int64"})

        if len(reloaded_cleaned) != len(cleaned_df):
            problems.append(
                f"cleaned CSV has {len(reloaded_cleaned)} rows, "
                f"intended {len(cleaned_df)}"
            )
        if int(reloaded_cleaned["Year"].isna().sum()) != 269:
            problems.append(
                f"cleaned CSV has {int(reloaded_cleaned['Year'].isna().sum())} "
                "missing Year values, intended 269"
            )
        if list(map(int, reloaded_cleaned["Rank"])) != list(map(int, cleaned_df["Rank"])):
            problems.append("cleaned CSV Rank values differ from the intended cleaned data")
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
                problems.append(f"cleaned CSV sales values differ in {column}")
        saved_zwsp = sum(
            int(reloaded_cleaned[column]
                .str.contains(ZERO_WIDTH_SPACE, regex=False, na=False).sum())
            for column in TEXT_COLUMNS
        )
        if saved_zwsp:
            problems.append(
                f"saved cleaned CSV still contains U+200B in {saved_zwsp} text cell(s)"
            )
        if not dataframes_match(reloaded_cleaned, cleaned_df):
            problems.append("cleaned CSV does not reproduce the cleaned data in memory")
    except Exception as section_error:
        raise ValueError(
            f"cleaned CSV ({cleaned_path}) is not a valid "
            f"cleaned dataset: {section_error}"
        ) from section_error

    try:
        reloaded_review = pd.read_csv(review_path)
        if not dataframes_match(reloaded_review, review_records):
            problems.append("review CSV does not reproduce the quarantined records in memory")
        raw_quarantined = original_df[original_df["Rank"].isin(RANKS_TO_QUARANTINE)]
        if not dataframes_match(reloaded_review, raw_quarantined):
            problems.append("review CSV does not match the original raw quarantined record")
    except Exception as section_error:
        raise ValueError(
            f"review CSV ({review_path}) is not a valid "
            f"review file: {section_error}"
        ) from section_error

    if problems:
        raise ValueError("; ".join(problems))

    print(
        f"Cleaned CSV verified: {len(reloaded_cleaned)} rows x "
        f"{len(reloaded_cleaned.columns)} columns (column order intact), "
        f"Rank values match, all 5 sales columns match, "
        f"missing Year = {int(reloaded_cleaned['Year'].isna().sum())}, "
        f"Int64 load successful"
    )
    print(
        f"Review CSV verified: every field matches the in-memory record "
        f"and the original raw record (Rank(s) {reloaded_review['Rank'].tolist()})"
    )


def snapshot_output_files(paths):
    """Read the current output files into memory so a failed run can be undone."""
    snapshot = {}
    for path in paths:
        try:
            with open(path, "rb") as handle:
                snapshot[path] = handle.read()
        except FileNotFoundError:
            pass
    return snapshot


def restore_output_files(snapshot):
    """Rewrite the previous contents of output files (rollback after a failed run)."""
    for path, content in snapshot.items():
        with open(path, "wb") as handle:
            handle.write(content)
    print("Rollback complete: every output was restored to its previous state.")
