"""Persist source provenance and small factual extracts, not copied marketing pages."""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "surface": "https://www.microsoft.com/en-us/surface/devices/surface-laptop-ultra",
    "annual": "https://www.microsoft.com/investor/reports/ar25/index.html",
}


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Copilot-HOL/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def main():
    for name, url in SOURCES.items():
        raw = fetch(url)
        soup = BeautifulSoup(raw, "html.parser")
        lab = "Lab2" if name == "surface" else "Lab3"
        folder = ROOT / lab / "Code" / "data"
        folder.mkdir(parents=True, exist_ok=True)
        provenance = {
            "url": url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "title": soup.title.get_text(" ", strip=True) if soup.title else name,
        }
        (folder / "source.json").write_text(json.dumps(provenance, indent=2))
        if name == "annual":
            wanted = []
            for i, table in enumerate(soup.find_all("table")):
                text = table.get_text(" ", strip=True)
                if ("281,724" in text or "128,528" in text or
                        ("120,810" in text and "106,820" in text)):
                    rows = [[cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
                            for row in table.find_all("tr")]
                    wanted.append({"table": i, "rows": rows})
            (folder / "tables.json").write_text(json.dumps(wanted, ensure_ascii=False, indent=2))
            print(json.dumps(wanted, ensure_ascii=False)[:22000])
        else:
            facts = [
                "15-inch touchscreen display",
                "Three USB-C ports, USB-A, HDMI, SD card reader, headphone jack",
                "Local AI workloads and 3D graphics",
                "Repair guidance and upgradeable storage; availability varies by market",
            ]
            for token in ("15", "USB-C", "HDMI", "local"):
                if token.lower() not in soup.get_text(" ", strip=True).lower():
                    raise ValueError(f"Surface source no longer contains {token}; review claims.")
            (folder / "facts.json").write_text(json.dumps({"facts": facts, "source": url}, indent=2))


if __name__ == "__main__":
    main()
