import argparse
import subprocess
import sys
from pathlib import Path

def run(cmd):
    print("\n$", " ".join(cmd))
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("profile")
    p.add_argument("files", nargs="+")

    p = sub.add_parser("index")
    p.add_argument("--s1", required=True)
    p.add_argument("--s2", required=True)
    p.add_argument("--s3", required=True)
    p.add_argument("--db", default="work/train.sqlite")

    p = sub.add_parser("pairs")
    p.add_argument("--db", required=True)
    p.add_argument("--truth", required=True)
    p.add_argument("--out", default="work/pairs.csv")
    p.add_argument("--s1-limit", type=int)
    p.add_argument("--negatives", type=int, default=15)

    p = sub.add_parser("train")
    p.add_argument("--pairs", required=True)
    p.add_argument("--model", default="work/model.joblib")
    p.add_argument("--validation", default="work/validation.csv")

    p = sub.add_parser("threshold")
    p.add_argument("--validation", required=True)

    a = ap.parse_args()
    py = sys.executable

    if a.cmd == "profile":
        run([py, "src/profile.py", *a.files])
    elif a.cmd == "index":
        run([py, "src/build_indexes.py", "--s1", a.s1, "--s2", a.s2, "--s3", a.s3, "--db", a.db])
    elif a.cmd == "pairs":
        cmd = [py, "src/create_pairs.py", "--db", a.db, "--truth", a.truth,
               "--out", a.out, "--negatives", str(a.negatives)]
        if a.s1_limit:
            cmd += ["--s1-limit", str(a.s1_limit)]
        run(cmd)
    elif a.cmd == "train":
        run([py, "src/train.py", "--pairs", a.pairs, "--model", a.model, "--validation", a.validation])
    elif a.cmd == "threshold":
        run([py, "src/threshold.py", "--validation", a.validation])
