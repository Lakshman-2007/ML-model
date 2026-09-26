import argparse
import pandas as pd

def f05(p, r):
    return 0.0 if p == 0 and r == 0 else 1.25*p*r/(.25*p+r)

def score(df, threshold):
    vals = []
    for sid, g in df.groupby("source1_entity_id", sort=False):
        pred = set(g.loc[g.score >= threshold, "candidate_entity_id"])
        true = set(g.loc[g.label == 1, "candidate_entity_id"])
        tp = len(pred & true)
        fp = len(pred - true)
        fn = len(true - pred)
        if not pred and not true:
            vals.append(1.0)
            continue
        p = tp/(tp+fp) if tp+fp else 0
        r = tp/(tp+fn) if tp+fn else 0
        vals.append(f05(p, r))
    return sum(vals)/len(vals)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--validation", required=True)
    a = ap.parse_args()
    df = pd.read_csv(a.validation)
    best = (0, -1)
    for t in [i/1000 for i in range(500, 1000)]:
        s = score(df, t)
        if s > best[1]:
            best = (t, s)
    print(f"best_threshold={best[0]:.3f}")
    print(f"validation_macro_F0.5={best[1]:.6f}")
