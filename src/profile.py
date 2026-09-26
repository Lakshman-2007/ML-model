import argparse
from pathlib import Path
import pandas as pd

def profile(path):
    print("\n", "=" * 70)
    print(path)
    total = 0
    missing = {"business_name": 0, "business_address": 0, "country": 0}
    countries = {}
    unique_ids = set()

    for chunk in pd.read_csv(
        path, sep="\t", dtype=str, keep_default_na=False,
        chunksize=250_000
    ):
        total += len(chunk)
        unique_ids.update(chunk.entity_id)
        for col in missing:
            missing[col] += int((chunk[col].str.strip() == "").sum())
        for k, v in chunk.country.value_counts().items():
            countries[k] = countries.get(k, 0) + int(v)

    print("rows:", total)
    print("unique IDs:", len(unique_ids))
    print("missing:", missing)
    print("countries:", countries)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()
    for f in args.files:
        profile(f)
