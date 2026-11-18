import pandas as pd

from src.analysis import CLEANED_DATA_PATH, RAW_DATA_PATH, REGIONS, GenreSummary, RegionalComparison


def main():
    before = pd.read_csv(RAW_DATA_PATH)
    after = pd.read_csv(CLEANED_DATA_PATH, dtype={"Year": "Int64"})

    print("=== Rows ===")
    print(f"before: {len(before)}  after: {len(after)}  removed: {len(before) - len(after)}")
    print("\nRows not in the cleaned data:")
    print(before[~before["Rank"].isin(after["Rank"])][["Rank", "Name", "Platform", "Year", "Genre", "Global_Sales"]]
          .to_string(index=False))

    print("\n=== Sales totals (millions) ===")
    totals = pd.DataFrame({"before": before[REGIONS + ["Global_Sales"]].sum(),
                           "after": after[REGIONS + ["Global_Sales"]].sum()})
    totals["change"] = totals["after"] - totals["before"]
    print(totals.round(2))

    print("\n=== Q1: best genre-platform pair per region ===")
    q1 = RegionalComparison().run(before).join(RegionalComparison().run(after), suffixes=("_before", "_after"))
    print(q1)

    print("\n=== Q2: genre totals and averages ===")
    q2 = GenreSummary().run(before).join(GenreSummary().run(after), suffixes=("_before", "_after"))
    print(q2.round(4).to_string())


if __name__ == "__main__":
    main()
