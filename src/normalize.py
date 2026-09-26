import re
import unicodedata

try:
    from unidecode import unidecode
except ImportError:
    def unidecode(x):
        return x

NAME_SUFFIXES = {
    "private", "pvt", "limited", "ltd", "llc", "inc", "incorporated",
    "corporation", "corp", "company", "co", "plc", "llp", "gmbh"
}

ABBR = {
    "road": "rd", "street": "st", "avenue": "ave", "boulevard": "blvd",
    "lane": "ln", "highway": "hwy", "private": "pvt", "limited": "ltd",
    "corporation": "corp", "incorporated": "inc", "company": "co"
}

def norm(s):
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).lower().strip()
    s = unidecode(s)
    s = s.replace("&", " and ")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def name(s):
    toks = [ABBR.get(x, x) for x in norm(s).split()]
    toks = [x for x in toks if x not in NAME_SUFFIXES]
    return " ".join(toks)

def address(s):
    toks = [ABBR.get(x, x) for x in norm(s).split()]
    return " ".join(toks)

def tokens(s):
    return set(norm(s).split())

def name_tokens(s):
    return set(name(s).split())

def numbers(s):
    return set(re.findall(r"\b\d+\b", norm(s)))

def postal(s):
    return set(re.findall(r"\b\d{5,6}(?:-\d{4})?\b", norm(s)))

def prefix(s, n=3):
    return name(s).replace(" ", "")[:n]
