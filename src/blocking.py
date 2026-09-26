from collections import Counter

MAX_TOKEN_POSTINGS = 150
MAX_PREFIX_POSTINGS = 500

def get_candidates(con, s1, target):
    # s1 tuple: entity_id, raw name, raw address, country, norm_name, norm_address, prefix
    eid, raw_name, raw_address, country, nn, na, pref = s1
    out = Counter()

    # A. Exact normalized name is very strong.
    for (cid,) in con.execute(
        f"SELECT entity_id FROM {target} WHERE country=? AND norm_name=? LIMIT 1000",
        (country, nn)
    ):
        out[cid] += 10

    # B. Rare-ish name-token postings.
    toks = [t for t in set(nn.split()) if len(t) >= 4]
    for tok in toks:
        rows = con.execute(
            f"SELECT entity_id FROM {target}_tokens WHERE token=? LIMIT ?",
            (tok, MAX_TOKEN_POSTINGS + 1)
        ).fetchall()
        if len(rows) <= MAX_TOKEN_POSTINGS:
            for (cid,) in rows:
                out[cid] += 3

    # C. Prefix block.
    if pref:
        for (cid,) in con.execute(
            f"SELECT entity_id FROM {target} WHERE country=? AND name_prefix=? LIMIT ?",
            (country, pref, MAX_PREFIX_POSTINGS)
        ):
            out[cid] += 1

    # D. Postal block.
    import re
    postals = set(re.findall(r"\b\d{5,6}(?:-\d{4})?\b", na))
    for p in postals:
        for (cid,) in con.execute(
            f"SELECT entity_id FROM {target}_postals WHERE postal=? LIMIT ?",
            (p, MAX_TOKEN_POSTINGS)
        ):
            out[cid] += 4

    # Return ranked candidate IDs. The score here is ONLY blocking evidence.
    return [cid for cid, _ in out.most_common()]
