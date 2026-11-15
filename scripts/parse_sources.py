"""Split the EU and US control lists into one JSON record per entry."""
import json, re, warnings
from pathlib import Path
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from lxml import etree

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "entries"
OUT.mkdir(parents=True, exist_ok=True)
CODE = re.compile(r"^(\d[A-E]\d{3})(?=\s|$)\s*(.*)")   # "2B001 Machine tools", not "2B001.a. does not..."

def split_entries(lines, regime, source_file, version):
    entries, current = {}, None
    for line in lines:
        m = CODE.match(line)
        if m:
            code = m.group(1)
            current = {"id": f"{regime}-{code}", "regime": regime, "code": code,
                       "category": code[0], "title": m.group(2)[:200],
                       "lines": [m.group(2)] if m.group(2) else [],
                       "source_file": source_file, "version": version}
            # a code can appear twice (e.g. a contents list): keep the longer one later
            entries.setdefault(code, []).append(current)
        elif current is not None:
            current["lines"].append(line)
            if not current["title"]:
                current["title"] = line[:200]
    result = []
    for code, found in entries.items():
        best = next((e for e in found if len(" ".join(e["lines"])) > 30), found[0])
        best["text"] = "\n".join(best.pop("lines")).strip()
        result.append(best)
    return result

def clean(text):
    return [l.strip() for l in text.splitlines() if l.strip()]

# --- EU: Annex I only (from the "ANNEX I" heading to "ANNEX II")
eu_file = sorted(RAW.glob("eu_2021_821_*.html"))[-1]
soup = BeautifulSoup(eu_file.read_text(encoding="utf-8"), "lxml")
lines = clean(soup.get_text("\n"))
start = next(i for i, l in enumerate(lines) if l.upper() == "ANNEX I")
end = next((i for i, l in enumerate(lines[start + 1:], start + 1) if l.upper().startswith("ANNEX II")), len(lines))
eu = split_entries(lines[start:end], "EU", eu_file.name, "2026-09-21")

# --- US: whole Part 774 XML, then drop the 600 series and x515 (military/space, ex-ITAR)
us_file = sorted(RAW.glob("us_ear_part774_*.xml"))[-1]
tree = etree.parse(str(us_file))
lines = clean("\n".join(t for t in tree.getroot().itertext()))
us_version = us_file.stem.split("_")[-1]
us = [e for e in split_entries(lines, "US", us_file.name, us_version)
      if e["code"][2] != "6" and e["code"][2:] != "515"]

# --- save and report
for name, entries in (("eu", eu), ("us", us)):
    with open(OUT / f"{name}.jsonl", "w", encoding="utf-8") as f:
        for e in sorted(entries, key=lambda e: e["code"]):
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    empty = sum(1 for e in entries if len(e["text"]) < 30)
    print(f"{name.upper()}: {len(entries)} entries, {empty} suspiciously short")
    for code in ("2B001", "3A001", "5A002"):
        e = next((x for x in entries if x["code"] == code), None)
        print(f"  {code}: " + (e["text"][:150].replace("\n", " ") + "..." if e else "NOT FOUND"))
