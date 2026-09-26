import argparse
import sqlite3
from pathlib import Path

import joblib
import pandas as pd

from blocking import get_candidates
from features import make_features
from train import FEATURES
from build_indexes import build_source, build_token_index

def predict(db, model_file, threshold, out_dir):
    con = sqlite3.connect(db)
    model = joblib.load(model_file)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    matches = []
    candidates_out = []

    cur = con.execute(
        "SELECT entity_id,business_name,business_address,country,norm_name,norm_address,name_prefix FROM s1"
    )

    for i, s1 in enumerate(cur, 1):
        ids = set(get_candidates(con, s1, "s2")) | set(get_candidates(con, s1, "s3"))
        ids = sorted(ids)
        candidates_out.append({
            "source1_entity_id": s1[0],
            "candidate_entity_ids": ",".join(ids)
        })

        scored = []
        for cid in ids:
            table = "s2" if cid.startswith("S2-") else "s3"
            target = con.execute(
                f"""SELECT entity_id,business_name,business_address,country,
                           norm_name,norm_address,name_prefix
                    FROM {table} WHERE entity_id=?""", (cid,)
            ).fetchone()
            if target:
                scored.append((cid, make_features(s1, target)))

        if scored:
            X = pd.DataFrame([f for _, f in scored])[FEATURES]
            probs = model.predict_proba(X)[:, 1]
            chosen = [cid for (cid, _), p in zip(scored, probs) if p >= threshold]
        else:
            chosen = []

        matches.append({
            "source1_entity_id": s1[0],
            "matched_entity_ids": ",".join(sorted(set(chosen)))
        })

        if i % 10000 == 0:
            print("predicted:", i)

    pd.DataFrame(matches).to_csv(
        out/"matching_results.tsv", sep="\t", index=False, lineterminator="\n"
    )
    pd.DataFrame(candidates_out).to_csv(
        out/"candidate_pairs.tsv", sep="\t", index=False, lineterminator="\n"
    )
    con.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--s1", required=True)
    ap.add_argument("--s2", required=True)
    ap.add_argument("--s3", required=True)
    ap.add_argument("--db", default="work/test.sqlite")
    ap.add_argument("--model", required=True)
    ap.add_argument("--threshold", type=float, required=True)
    ap.add_argument("--out", default="output")
    a = ap.parse_args()

    Path(a.db).parent.mkdir(parents=True, exist_ok=True)
    build_source(a.s1, a.db, "s1")
    build_source(a.s2, a.db, "s2")
    build_source(a.s3, a.db, "s3")
    build_token_index(a.db, "s2")
    build_token_index(a.db, "s3")
    predict(a.db, a.model, a.threshold, a.out)

if __name__ == "__main__":
    main()
