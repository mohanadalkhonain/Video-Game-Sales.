

import pandas as pd

from src.data_cleaning import (
    CLEANED_DATA_PATH,
    CLEANING_REPORT_PATH,
    RANKS_TO_REMOVE,
    REVIEW_FILE_PATH,
    clean_data,
    inspect_data,
    load_data,
    restore_output_files,
    sales_reconciliation,
    save_cleaned_data,
    save_review_records,
    snapshot_output_files,
    validate_outputs,
    verify_saved_output_files,
    write_cleaning_report,
)

OUTPUT_PATHS = [CLEANED_DATA_PATH, REVIEW_FILE_PATH, CLEANING_REPORT_PATH]


def main():
    print("=" * 70)
    print("VIDEO GAME SALES - DATA CLEANING WORKFLOW")
    print("=" * 70)

    print("\nLoading and cleaning...")
    original_df = load_data()
    before_stats = inspect_data(original_df)
    print(f"Raw dataset: {before_stats['rows']} rows x {len(before_stats['columns'])} columns")

    cleaned_df, review_records, action_log = clean_data(original_df)
    after_stats = inspect_data(cleaned_df)
    print(f"Cleaned dataset: {after_stats['rows']} rows")
    print(f"Quarantined records: {len(review_records)} (saved for review, not deleted)")

    removed_rows = original_df[original_df["Rank"].isin(RANKS_TO_REMOVE)]
    reconciliation = sales_reconciliation(
        original_df, cleaned_df, review_records, removed_rows
    )

    print("\nValidating results before writing any file...")
    all_passed, _, checks = validate_outputs(original_df, cleaned_df, review_records)
    if not all_passed:
        print("The validation checklist FAILED:")
        for description, passed, _ in checks:
            if not passed:
                print("  -", description)
        raise SystemExit(
            "Validation failed: nothing was written and existing outputs "
            "are unchanged."
        )

    snapshot = snapshot_output_files(OUTPUT_PATHS)

    try:
        print("\nSaving outputs (previous outputs were snapshotted)...")
        save_cleaned_data(cleaned_df)
        save_review_records(review_records)
        write_cleaning_report(
            before_stats=before_stats,
            after_stats=after_stats,
            action_log=action_log,
            original_df=original_df,
            cleaned_df=cleaned_df,
            removed_rows=removed_rows,
            review_df=review_records,
            reconciliation=reconciliation,
        )

        print("\nVerifying the saved files' actual contents...")
        verify_saved_output_files(
            cleaned_df, review_records, original_df, *OUTPUT_PATHS
        )

    except Exception as error:
        print("\n" + "!" * 3 + " WORKFLOW FAILED " + "!" * 3)
        print("Reason:", error)
        print("Restoring the previous outputs...")
        restore_output_files(snapshot)
        raise SystemExit(1)

    reloaded = pd.read_csv(CLEANED_DATA_PATH, dtype={"Year": "Int64"})
    print("\nReload check on the published dataset:")
    print(f"  {len(reloaded)} rows x {len(reloaded.columns)} columns")
    print("  Missing Year values:", int(reloaded["Year"].isna().sum()))
    print("  Year dtype:", reloaded["Year"].dtype)

    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETE")
    print("=" * 70)
    print("All validation checks passed and results were saved.")
    print("Outputs:")
    print("  -", CLEANED_DATA_PATH)
    print("  -", REVIEW_FILE_PATH)
    print("  -", CLEANING_REPORT_PATH)


if __name__ == "__main__":
    main()
