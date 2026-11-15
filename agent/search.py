"""Simple keyword search over the parsed control entries."""
import json, math, re
from collections import Counter
from pathlib import Path

ENTRIES = Path(__file__).resolve().parent.parent / "data" / "entries"
WORD = re.compile(r"[a-z0-9]+")
SYNONYMS = {"micrometre": "um", "micrometer": "um", "micrometres": "um", "micrometers": "um",
            "micron": "um", "microns": "um", "axes": "axis", "tools": "tool", "machines": "machine"}

def tokens(text):
    text = text.lower().replace("µm", " um ").replace("μm", " um ")
    return [SYNONYMS.get(t, t) for t in WORD.findall(text)]

def load(regime="both"):
    files = {"EU": ["eu"], "US": ["us"], "both": ["eu", "us"]}[regime]
    return [json.loads(l) for f in files for l in open(ENTRIES / f"{f}.jsonl", encoding="utf-8")]

def search(query, regime="both", limit=5):
    entries = load(regime)
    docs = [Counter(tokens(e["title"] * 3 + " " + e["text"])) for e in entries]  # title counts more
    n = len(docs)
    q = set(tokens(query))
    df = {t: sum(1 for d in docs if t in d) for t in q}
    scored = []
    for e, d in zip(entries, docs):
        s = sum(math.log(1 + n / df[t]) * (1 + math.log(d[t])) for t in q if d[t])
        if e["code"].lower() in q:          # exact code match wins
            s += 100
        if s > 0:
            scored.append((s, e))
    return [e for s, e in sorted(scored, key=lambda x: -x[0])[:limit]]

if __name__ == "__main__":
    import sys
    for e in search(" ".join(sys.argv[1:])):
        print(f"[{e['regime']} {e['code']}] {e['title'][:90]}")
