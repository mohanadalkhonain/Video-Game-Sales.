import pandas as pd

from src.data_cleaning import (
    CLEANED_DATA_PATH,
    CLEANING_REPORT_PATH,
    RANKS_TO_REMOVE,
    REVIEW_FILE_PATH,
    clean_data,
    discard_pending_outputs,
    fetch_raw_data,
    inspect_data,
    load_data,
    publish_pending_outputs,
    sales_reconciliation,
    save_cleaned_data,
    save_review_records,
    validate_outputs,
    verify_saved_output_files,
    write_cleaning_report,
)


def main():
    print("=" * 70)
    print("VIDEO GAME SALES - DATA CLEANING WORKFLOW (Member 1)")
    print("=" * 70)

    print("\nLoading and cleaning...")
    fetch_raw_data()

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

    print("\nValidating results in memory (before writing any file)...")
    all_passed, _, checks = validate_outputs(original_df, cleaned_df, review_records)
    failed_checks = [description for description, passed, _ in checks if not passed]
    if not all_passed:
        print("The validation checklist FAILED:")
        for description in failed_checks:
            print("  -", description)
        raise SystemExit(
            "Validation failed: nothing was written and existing outputs "
            "are unchanged."
        )

    pending_cleaned = CLEANED_DATA_PATH + ".pending"
    pending_review = REVIEW_FILE_PATH + ".pending"
    pending_report = CLEANING_REPORT_PATH + ".pending"
    pending_and_final = [
        (pending_cleaned, CLEANED_DATA_PATH),
        (pending_review, REVIEW_FILE_PATH),
        (pending_report, CLEANING_REPORT_PATH),
    ]
    pending_paths = [pending for pending, _ in pending_and_final]

    try:
        print("\nStaging outputs under temporary names (final files untouched)...")
        save_cleaned_data(cleaned_df, pending_cleaned)
        save_review_records(review_records, pending_review)
        write_cleaning_report(
            before_stats=before_stats,
            after_stats=after_stats,
            action_log=action_log,
            original_df=original_df,
            removed_rows=removed_rows,
            review_df=review_records,
            reconciliation=reconciliation,
            original_row_count=before_stats["rows"],
            report_path=pending_report,
        )

        print("\nVerifying the staged files' actual contents...")
        verify_saved_output_files(
            cleaned_df, review_records, original_df,
            pending_cleaned, pending_review, pending_report,
        )

        print("\nAll checks passed - publishing outputs...")
        publish_pending_outputs(pending_and_final)

    except Exception as error:
        print("\n" + "!" * 3 + " WORKFLOW FAILED " + "!" * 3)
        print("Reason:", error)
        print("Publishing was stopped; existing output files were not replaced.")
        discard_pending_outputs(pending_paths)
        raise SystemExit(1)

    reloaded = pd.read_csv(CLEANED_DATA_PATH, dtype={"Year": "Int64"})
    print("\nReload check on the PUBLISHED dataset:")
    print(f"  {len(reloaded)} rows x {len(reloaded.columns)} columns")
    print("  Missing Year values:", int(reloaded["Year"].isna().sum()))
    print("  Year dtype:", reloaded["Year"].dtype)

    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETE")
    print("=" * 70)
    print("All validation checks passed and results were published.")
    print("Outputs:")
    print("  -", CLEANED_DATA_PATH)
    print("  -", REVIEW_FILE_PATH)
    print("  -", CLEANING_REPORT_PATH)


if __name__ == "__main__":
    main()
