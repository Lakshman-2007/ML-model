from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dataset"
TRAIN = DATA / "train"
TEST = DATA / "test"
WORK = ROOT / "work"
OUTPUT = ROOT / "output"

for p in (WORK, OUTPUT):
    p.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "name_ratio", "name_token_set", "name_token_sort", "name_prefix_ratio",
    "address_ratio", "address_token_set", "address_token_sort",
    "postal_match", "number_overlap", "country_match",
    "name_exact", "address_exact", "name_token_jaccard", "address_token_jaccard"
]
