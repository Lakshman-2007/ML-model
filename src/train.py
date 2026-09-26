import argparse
from pathlib import Path
import joblib
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.model_selection import GroupShuffleSplit

FEATURES = [
    "name_ratio", "name_token_set", "name_token_sort", "name_prefix_ratio",
    "address_ratio", "address_token_set", "address_token_sort",
    "postal_match", "number_overlap", "country_match",
    "name_exact", "address_exact", "name_token_jaccard", "address_token_jaccard"
]

def run(pairs, model_out, validation_out):
    df = pd.read_csv(pairs)
    df = df.dropna(subset=FEATURES + ["label", "source1_entity_id"])
    split = GroupShuffleSplit(n_splits=1, test_size=.2, random_state=42)
    tr, va = next(split.split(df, groups=df.source1_entity_id))

    model = LGBMClassifier(
        objective="binary",
        n_estimators=500,
        learning_rate=.05,
        num_leaves=63,
        max_depth=-1,
        subsample=.85,
        colsample_bytree=.85,
        reg_lambda=2.0,
        n_jobs=-1,
        random_state=42,
        verbosity=-1
    )
    model.fit(df.iloc[tr][FEATURES], df.iloc[tr].label.astype(int))

    val = df.iloc[va][["source1_entity_id", "candidate_entity_id", "label"]].copy()
    val["score"] = model.predict_proba(df.iloc[va][FEATURES])[:, 1]

    Path(model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_out)
    val.to_csv(validation_out, index=False)
    print("model:", model_out)
    print("validation:", validation_out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--model", default="work/model.joblib")
    ap.add_argument("--validation", default="work/validation.csv")
    a = ap.parse_args()
    run(a.pairs, a.model, a.validation)
