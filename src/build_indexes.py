import argparse
import sqlite3
from pathlib import Path
import pandas as pd

from normalize import name, address, tokens, postal, prefix

def build_source(path, db, table):
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=OFF")
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(f"""
        CREATE TABLE {table}(
            entity_id TEXT PRIMARY KEY,
            business_name TEXT,
            business_address TEXT,
            country TEXT,
            norm_name TEXT,
            norm_address TEXT,
            name_prefix TEXT
        )
    """)
    con.execute(f"CREATE INDEX {table}_name ON {table}(norm_name)")
    con.execute(f"CREATE INDEX {table}_prefix_country ON {table}(name_prefix,country)")
    con.execute(f"CREATE INDEX {table}_country ON {table}(country)")

    sql = f"INSERT INTO {table} VALUES (?,?,?,?,?,?,?)"
    for chunk in pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False,
                             chunksize=100_000):
        rows = []
        for r in chunk.itertuples(index=False):
            rows.append((
                r.entity_id, r.business_name, r.business_address, r.country,
                name(r.business_name), address(r.business_address),
                prefix(r.business_name)
            ))
        con.executemany(sql, rows)
        con.commit()
        print(table, "loaded", len(rows))
    con.close()

def build_token_index(db, table):
    con = sqlite3.connect(db)
    con.execute("PRAGMA synchronous=OFF")
    ti = f"{table}_tokens"
    pi = f"{table}_postals"
    con.execute(f"DROP TABLE IF EXISTS {ti}")
    con.execute(f"DROP TABLE IF EXISTS {pi}")
    con.execute(f"CREATE TABLE {ti}(token TEXT, entity_id TEXT)")
    con.execute(f"CREATE TABLE {pi}(postal TEXT, entity_id TEXT)")
    con.execute(f"CREATE INDEX {ti}_token ON {ti}(token)")
    con.execute(f"CREATE INDEX {pi}_postal ON {pi}(postal)")

    cur = con.execute(
        f"SELECT entity_id,norm_name,norm_address FROM {table}"
    )
    batch_t, batch_p = [], []
    n = 0
    for eid, nn, na in cur:
        # Store name tokens. Very short tokens are intentionally ignored.
        for t in set(x for x in nn.split() if len(x) >= 4):
            batch_t.append((t, eid))
        for p in postal(na):
            batch_p.append((p, eid))
        n += 1
        if len(batch_t) >= 100_000:
            con.executemany(f"INSERT INTO {ti} VALUES (?,?)", batch_t)
            con.executemany(f"INSERT INTO {pi} VALUES (?,?)", batch_p)
            con.commit()
            batch_t, batch_p = [], []
    if batch_t:
        con.executemany(f"INSERT INTO {ti} VALUES (?,?)", batch_t)
    if batch_p:
        con.executemany(f"INSERT INTO {pi} VALUES (?,?)", batch_p)
    con.commit()
    con.close()
    print("token index built:", table, n)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--s1", required=True)
    ap.add_argument("--s2", required=True)
    ap.add_argument("--s3", required=True)
    ap.add_argument("--db", default="work/entities.sqlite")
    args = ap.parse_args()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)

    build_source(args.s1, args.db, "s1")
    build_source(args.s2, args.db, "s2")
    build_source(args.s3, args.db, "s3")
    build_token_index(args.db, "s2")
    build_token_index(args.db, "s3")
