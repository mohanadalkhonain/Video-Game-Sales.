import os

import numpy as np
import pandas as pd

REGIONS = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "vgsales.csv")
CLEANED_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "vgsales_cleaned.csv")


class SalesAnalysis:
    def run(self, data):
        raise NotImplementedError("Subclasses must override run()")


class GenreSummary(SalesAnalysis):
    # Q2: total and average global sales per genre
    def run(self, data):
        out = (data.groupby("Genre")["Global_Sales"]
               .agg(total="sum", average="mean")
               .sort_values("total", ascending=False))
        out["avg_rank"] = out["average"].rank(ascending=False).astype(int)  # 1 = highest average
        return out


class RegionalComparison(SalesAnalysis):
    # Q1: best-selling genre-platform pair in each region
    def run(self, data):
        M = data[REGIONS].to_numpy()  # one row per release, one column per region
        assert not np.isnan(M).any(), "sales columns contain NaN"

        # region totals and average sales per release
        self.region_stats = pd.DataFrame(
            {"total": M.sum(axis=0), "average": M.mean(axis=0)}, index=REGIONS)

        # v marks the releases of one pair (1 = match, 0 = not); v @ M = that pair's 4 regional totals
        rows = {}
        for g, p in data[["Genre", "Platform"]].drop_duplicates().itertuples(index=False):
            v = ((data["Genre"] == g) & (data["Platform"] == p)).to_numpy().astype(int)
            rows[(g, p)] = v @ M
        self.pair_sales = pd.DataFrame(rows, index=REGIONS).T

        # self-check: matrix result must equal pandas groupby
        ref = data.groupby(["Genre", "Platform"])[REGIONS].sum()
        assert np.allclose(self.pair_sales.sort_index().to_numpy(), ref.sort_index().to_numpy())

        return pd.DataFrame({"best_pair": self.pair_sales.idxmax(),
                             "sales": self.pair_sales.max()})
