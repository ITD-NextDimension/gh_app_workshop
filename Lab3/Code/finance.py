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
    expected_metrics = {
        "Revenue": {"2025": 281724, "2024": 245122},
        "Operating income": {"2025": 128528, "2024": 109433},
        "Net income": {"2025": 101832, "2024": 88136},
    }
    for metric, years in expected_metrics.items():
        for year, expected in years.items():
            if metrics[metric][year] != expected:
                raise ValueError(f"{metric} FY{year} 不符合指定年报中的核对值。")
    reconciliation = {}
    margins = {}
    for year in ("2025", "2024"):
        revenue_sum = sum(s["revenue"][year] for s in segments)
        income_sum = sum(s["operating_income"][year] for s in segments)
        if revenue_sum != metrics["Revenue"][year]:
            raise ValueError(f"FY{year} 业务分部营收与总营收不一致，请检查源表。")
        if income_sum != metrics["Operating income"][year]:
            raise ValueError(f"FY{year} 业务分部营业利润与总营业利润不一致，请检查源表。")
        reconciliation[year] = {
            "segment_revenue_sum": revenue_sum,
            "reported_revenue": metrics["Revenue"][year],
            "segment_operating_income_sum": income_sum,
            "reported_operating_income": metrics["Operating income"][year],
        }
        margins[year] = metrics["Operating income"][year] / metrics["Revenue"][year] * 100
        for segment in segments:
            segment.setdefault("bar_pct", {})[year] = (
                segment["revenue"][year] / max(s["revenue"][year] for s in segments) * 100
            )
    source = json.loads((ROOT / "data/source.json").read_text())
    if source.get("url") != "https://www.microsoft.com/investor/reports/ar25/index.html":
        raise ValueError("数据来源不是指定的 Microsoft FY2025 年报。")
    return {"metrics": metrics, "segments": segments, "reconciliation": reconciliation,
            "validation": {
                "reported_metrics_match": True,
                "segment_totals_match": True,
                "operating_margin_pct": margins,
            },
            "unit": "USD millions", "period": "Fiscal year ended June 30",
            "source": source,
            "comparability": "FY2024 segment comparatives are the recast figures presented in AR2025."}


def _view(data, year, segment):
    if year not in ("2025", "2024"):
        raise ValueError("只支持 FY2025 和 FY2024")
    revenue = data["metrics"]["Revenue"][year]
    income = data["metrics"]["Operating income"][year]
    previous = data["metrics"]["Revenue"]["2024"]
    net_income = data["metrics"]["Net income"][year]
    bar_pct = 100
    if segment != "all":
        selected = next((s for s in data["segments"] if s["name"] == segment), None)
        if not selected:
            raise ValueError("Unknown segment")
        revenue = selected["revenue"][year]
        income = selected["operating_income"][year]
        previous = selected["revenue"]["2024"]
        net_income = None
        bar_pct = selected["bar_pct"][year]
    return {"year": year, "segment": segment, "revenue": revenue,
            "operating_income": income, "net_income": net_income,
            "margin_pct": income / revenue * 100, "bar_pct": bar_pct,
            "yoy_pct": (revenue / previous - 1) * 100 if year == "2025" else None}


def views(data=None):
    data = data or dataset()
    segments = ["all", *(segment["name"] for segment in data["segments"])]
    return {year: {segment: _view(data, year, segment) for segment in segments}
            for year in ("2025", "2024")}


def view(year="2025", segment="all"):
    return _view(dataset(), year, segment)


if __name__ == "__main__":
    print(json.dumps(dataset(), ensure_ascii=False, indent=2))
