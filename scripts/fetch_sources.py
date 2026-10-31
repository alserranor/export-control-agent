"""Download the official source texts into data/raw/."""
from pathlib import Path
import requests

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "export-control-agent (research)"}

# --- EU: EUR-Lex blocks scripts, so this file is saved by hand from the browser
eu = RAW / "eu_2021_821_consolidated_20260921.html"
if eu.exists() and eu.stat().st_size > 100_000:
    print(f"EU file present ({eu.stat().st_size/1e6:.1f} MB)")
else:
    print("EU file missing or empty: download it in the browser (see SOURCES.md)")

# --- US: ask eCFR for the latest date it has, then download Part 774
titles = requests.get("https://www.ecfr.gov/api/versioner/v1/titles.json",
                      headers=HEADERS, timeout=60).json()["titles"]
latest = next(t for t in titles if t["number"] == 15)["up_to_date_as_of"]

url = f"https://www.ecfr.gov/api/versioner/v1/full/{latest}/title-15.xml?part=774"
r = requests.get(url, headers=HEADERS, timeout=120)
r.raise_for_status()
us = RAW / f"us_ear_part774_{latest.replace('-', '')}.xml"
us.write_bytes(r.content)
print(f"saved {us.name} ({len(r.content)/1e6:.1f} MB), eCFR as of {latest}")
