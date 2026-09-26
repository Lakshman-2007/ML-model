import argparse
import random
import sqlite3
from pathlib import Path

import pandas as pd

from blocking import get_candidates
from features import make_features

def read_truth(path):
    truth = {}
    for c in pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False,
                          chunksize=200_000):
        for r in c.itertuples(index=False):
            truth[r.source1_entity_id] = {
                x for x in r.matched_entity_ids.split(",") if x
            }
    return truth

def fetch(con, table, eid):
    return con.execute(
        f"""SELECT entity_id,business_name,business_address,country,
                   norm_name,norm_address,name_prefix
            FROM {table} WHERE entity_id=?""", (eid,)
    ).fetchone()

def build(db, truth_file, out, s1_limit=None, negatives=15):
    con = sqlite3.connect(db)
    truth = read_truth(truth_file)
    ids = list(truth)
    if s1_limit:
        ids = ids[:s1_limit]
    random.seed(42)

    result = []
    for i, sid in enumerate(ids, 1):
        s1 = fetch(con, "s1", sid)
        if not s1:
            continue

        positive = truth[sid]
        candidates = set()
        candidates.update(get_candidates(con, s1, "s2"))
        candidates.update(get_candidates(con, s1, "s3"))
        candidates |= positive

        hard = list(candidates - positive)
        # Prioritize blocking-strong negatives, then sample.
        random.shuffle(hard)
        hard = hard[:negatives]

        selected = [(x, 1) for x in positive] + [(x, 0) for x in hard]

        for cid, label in selected:
            table = "s2" if cid.startswith("S2-") else "s3"
            target = fetch(con, table, cid)
            if target:
                row = make_features(s1, target)
                row.update(source1_entity_id=sid, candidate_entity_id=cid, label=label)
                result.append(row)

        if i % 10000 == 0:
            print("S1 processed:", i, "pairs:", len(result))

    pd.DataFrame(result).to_csv(out, index=False)
    con.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--truth", required=True)
    ap.add_argument("--out", default="work/pairs.csv")
    ap.add_argument("--s1-limit", type=int)
    ap.add_argument("--negatives", type=int, default=15)
    a = ap.parse_args()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    build(a.db, a.truth, a.out, a.s1_limit, a.negatives)
