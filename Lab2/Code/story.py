"""Generate a fact-bounded six-scene video plan and Mandarin narration."""
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.agent import client, run_json

ROOT = Path(__file__).parent
PLAN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "story": {"type": "string"},
        "scenes": {"type": "array", "minItems": 6, "maxItems": 6, "items": {"type": "string"}},
        "checks": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["story", "scenes", "checks"],
}
EXECUTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "story": {"type": "string"},
        "scenes": {"type": "array", "minItems": 6, "maxItems": 6, "items": {"type": "string"}},
        "narration": {"type": "array", "minItems": 6, "maxItems": 6, "items": {"type": "string"}},
        "checks": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["story", "scenes", "narration", "checks"],
}


async def main():
    facts = json.loads((ROOT / "data/facts.json").read_text())
    async with client() as copilot:
        plan, plan_trace = await run_json(
            copilot,
            "video-planner",
            "这是只规划、不执行的 Plan 阶段。用中文规划一段 2 分钟、1080×1920、30fps 的竖屏产品介绍。"
            "总计 6 个镜头、每个 20 秒，顺序为：产品开场、本地 AI 与 3D 图形、15 英寸触控屏、"
            "触控创作、接口、维修与可升级存储。scenes 每项只写画面中文标题（最多16字），"
            "不用时间码。只用官网事实，不添加价格、性能或续航数字。返回故事、6 个标题和验收清单。\n"
            + json.dumps(facts, ensure_ascii=False),
            PLAN_SCHEMA,
            mode="plan",
        )
        execution, trace = await run_json(
            copilot,
            "video-producer",
            "已批准以下计划（教学自动审批，只涉及公开官网事实）。现在 Autopilot 输出恰好 6 个镜头标题，"
            "以及一段面向普通观众的普通话口播稿，按镜头顺序分成 6 段，每段约 75–100 个中文字符。"
            "标题最多16字。口播要自然、易懂，整体约 2 分钟；只陈述所给官网事实。"
            "可介绍本地 AI 与 3D 图形、15 英寸触控显示屏、接口、维修指引和可升级存储；"
            "明确功能/配置可能因市场而异。不要编造性能、价格、续航、分辨率或未提供的功能，"
            "接口只可明确说三个 USB-C；USB-A、HDMI、SD 卡读卡器和耳机插孔不要补充数量。"
            "不要把教学短片说成微软官方广告。六段分别对应计划中的六个镜头。"
            "不执行文件或网页操作，画面交由本地 HyperFrames 模板生成。\n"
            + json.dumps({"plan": plan, "facts": facts}, ensure_ascii=False),
            EXECUTION_SCHEMA,
        )
    if len(execution["scenes"]) != 6 or any(len(scene) > 16 for scene in execution["scenes"]):
        raise ValueError("必须恰好六个不超过16字的画面标题。")
    narration = execution["narration"]
    if len(narration) != 6 or any(not 65 <= len(paragraph) <= 120 for paragraph in narration):
        raise ValueError("口播稿必须按六个镜头分成六段，每段65至120字。")
    if not 450 <= sum(map(len, narration)) <= 700:
        raise ValueError("口播稿总长度应为450至700字，便于合成约两分钟旁白。")
    unsupported_port_count = re.compile(
        r"(?:一个|一组|一只|1\s*(?:个|组|只)?)\s*(?:USB-A|HDMI|SD(?:卡)?|耳机)",
        re.IGNORECASE,
    )
    if unsupported_port_count.search(" ".join(narration)):
        raise ValueError("口播稿不可为 USB-A、HDMI、SD 卡读卡器或耳机插孔添加未提供的数量。")
    (ROOT / "data/story.json").write_text(
        json.dumps(
            {"plan": plan, "plan_trace": plan_trace, "execution": execution, "trace": trace},
            ensure_ascii=False,
            indent=2,
        )
    )
    (ROOT / "data/narration.txt").write_text("\n\n".join(narration).strip() + "\n")
    print("Plan、Autopilot 与口播稿已保存：Lab2/Code/data/story.json、data/narration.txt")


if __name__ == "__main__":
    asyncio.run(main())
