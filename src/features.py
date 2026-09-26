from rapidfuzz.fuzz import ratio, token_set_ratio, token_sort_ratio
from normalize import name_tokens, tokens, numbers, postal

def jacc(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def make_features(a, b):
    # entity_id, raw_name, raw_address, country, norm_name, norm_address, prefix
    _, _, _, ca, na, aa, _ = a
    _, _, _, cb, nb, ab, _ = b

    nt1, nt2 = name_tokens(na), name_tokens(nb)
    at1, at2 = tokens(aa), tokens(ab)
    nums1, nums2 = numbers(aa), numbers(ab)
    p1, p2 = postal(aa), postal(ab)

    return {
        "name_ratio": ratio(na, nb) / 100,
        "name_token_set": token_set_ratio(na, nb) / 100,
        "name_token_sort": token_sort_ratio(na, nb) / 100,
        "name_prefix_ratio": ratio(na[:12], nb[:12]) / 100 if na and nb else 0,
        "address_ratio": ratio(aa, ab) / 100,
        "address_token_set": token_set_ratio(aa, ab) / 100,
        "address_token_sort": token_sort_ratio(aa, ab) / 100,
        "postal_match": float(bool(p1 and p2 and p1 & p2)),
        "number_overlap": jacc(nums1, nums2),
        "country_match": float(ca.lower().strip() == cb.lower().strip()),
        "name_exact": float(bool(na) and na == nb),
        "address_exact": float(bool(aa) and aa == ab),
        "name_token_jaccard": jacc(nt1, nt2),
        "address_token_jaccard": jacc(at1, at2),
    }
