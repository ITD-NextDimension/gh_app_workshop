"""Numbers are calculated in Python, not invented by an LLM."""
import json
from pathlib import Path

ROOT = Path(__file__).parent


def number(text):
    return float(text.replace("$", "").replace(",", "").strip())


def dataset():
    tables = json.loads((ROOT / "data/tables.json").read_text())
    summary = next(t["rows"] for t in tables if t["rows"][0][-1] == "Percentage Change"
                   and t["rows"][1][0] == "Revenue")
    metrics = {
        row[0]: {"2025": number(row[1]), "2024": number(row[2])}
        for row in summary[1:]
    }
    segments = []
    rows = next(t["rows"] for t in tables if t["rows"][0][0] == "(In millions)"
                and t["rows"][2][0] == "Productivity and Business Processes")
    for label in ("Productivity and Business Processes", "Intelligent Cloud", "More Personal Computing"):
        index = next(i for i, row in enumerate(rows) if row[0] == label)
        revenue, income = rows[index + 1], rows[index + 4]
        segments.append({"name": label,
                         "revenue": {"2025": number(revenue[1]), "2024": number(revenue[3])},
                         "operating_income": {"2025": number(income[1]), "2024": number(income[3])}})
    for year in ("2025", "2024"):
        if sum(s["revenue"][year] for s in segments) != metrics["Revenue"][year]:
            raise ValueError("业务分部与总营收不一致，请检查源表。")
    return {"metrics": metrics, "segments": segments,
            "unit": "USD millions", "period": "Fiscal year ended June 30",
            "source": json.loads((ROOT / "data/source.json").read_text()),
            "comparability": "FY2024 segment comparatives are the recast figures presented in AR2025."}


def view(year="2025", segment="all"):
    if year not in ("2025", "2024"):
        raise ValueError("只支持 FY2025 和 FY2024")
    data = dataset()
    revenue = data["metrics"]["Revenue"][year]
    income = data["metrics"]["Operating income"][year]
    previous = data["metrics"]["Revenue"]["2024"]
    if segment != "all":
        selected = next((s for s in data["segments"] if s["name"] == segment), None)
        if not selected:
            raise ValueError("Unknown segment")
        revenue = selected["revenue"][year]
        income = selected["operating_income"][year]
        previous = selected["revenue"]["2024"]
    return {"year": year, "segment": segment, "revenue": revenue, "operating_income": income,
            "margin_pct": income / revenue * 100,
            "yoy_pct": (revenue / previous - 1) * 100 if year == "2025" else None}


if __name__ == "__main__":
    print(json.dumps(dataset(), ensure_ascii=False, indent=2))
