import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.agent import client, run_json
from finance import dataset, view

ROOT = Path(__file__).parent
SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "findings": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {"heading": {"type": "string"}, "explanation": {"type": "string"},
                           "metric": {"type": "string"}},
            "required": ["heading", "explanation", "metric"]}},
        "caveat": {"type": "string"},
    },
    "required": ["title", "findings", "caveat"],
}


async def main():
    data = dataset()
    prompt = (
        "用中文给非财务专业同事写 3 条有依据的微软 FY2025 财报观察。"
        "只使用以下数字，金额单位为百万美元。引述 Revenue、Operating income、"
        "Net income、Diluted earnings per share 或分部名称作为 metric。"
        "区分营收、利润和利润率；不要将 FY2025 说成自然年；不要推断股价、预测或给投资建议。"
        "每条 explanation 写出所用数字或计算公式。不得创建子 Agent。返回符合 schema 的 JSON。\n"
        + json.dumps({"data": data, "calculated": view()}, ensure_ascii=False)
    )
    async with client() as copilot:
        result, trace = await run_json(copilot, "single-financial-analyst", prompt, SCHEMA)
    if len(result["findings"]) != 3:
        raise ValueError("期望恰好 3 条观察")
    result["trace"] = trace
    result["source"] = data["source"]["url"]
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    (output / "analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
