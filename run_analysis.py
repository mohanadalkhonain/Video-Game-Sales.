import pandas as pd

from src.analysis import CLEANED_DATA_PATH, GenreSummary, RegionalComparison


def main():
    data = pd.read_csv(CLEANED_DATA_PATH, dtype={"Year": "Int64"})

    # polymorphism: same run(data) call, different behaviour per class
    for obj in [GenreSummary(), RegionalComparison()]:
        print(f"\n=== {type(obj).__name__} ===")
        print(obj.run(data))

    print("\n=== Region totals and averages (NumPy) ===")
    print(obj.region_stats)

    print("\n=== Q2 answer ===")
    g = GenreSummary().run(data)
    top_total, top_avg = g["total"].idxmax(), g["average"].idxmax()
    print("Highest total:", top_total)
    print("Highest average:", top_avg)
    print("Same genre?", "Yes" if top_total == top_avg else "No")

    print("\n=== Q3: NA vs EU vs JP for the top 10 genre-platform pairs (by NA+EU+JP) ===")
    q3 = obj.pair_sales[["NA_Sales", "EU_Sales", "JP_Sales"]]
    q3 = q3.loc[q3.sum(axis=1).nlargest(10).index]
    shares = q3.div(q3.sum(axis=1), axis=0).mul(100).add_suffix("_%")
    print(q3.join(shares.round(1)).to_string())


if __name__ == "__main__":
    main()
