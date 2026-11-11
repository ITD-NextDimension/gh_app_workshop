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
            "触觉触控板与磁吸 USB-C 充电、接口、维修指引与可升级存储。scenes 每项只写画面中文标题"
            "（最多16字），不用时间码。只用给定官网事实；在开场和结尾提及预发布状态与地区差异，"
            "不得添加价格、续航、性能数字或其他未提供的规格。返回故事、6 个标题和验收清单。\n"
            + json.dumps(facts, ensure_ascii=False),
            PLAN_SCHEMA,
            mode="plan",
        )
        execution, trace = await run_json(
            copilot,
            "video-producer",
            "已批准以下计划（教学自动审批，只涉及公开官网事实）。现在 Autopilot 输出恰好 6 个镜头标题，"
            "以及一段自然、易懂、面向普通观众的普通话口播稿，按镜头顺序分成 6 段，每段约 75–100 个中文字符。"
            "标题最多16字。整体面向约 2 分钟成片；只陈述所给官网事实。六段依次对应产品开场、本地 AI 与 3D 图形、"
            "15 英寸触控屏、触觉触控板与磁吸 USB-C 充电、接口、维修指引与可升级存储。"
            "第一段和最后一段必须清楚说明这是微软标注的预发布产品，功能可能变化并因国家/地区而异。"
            "触控屏段必须说明只支持触控交互、不支持触控笔输入或 Surface Pen 兼容。"
            "接口只可明确说三个 USB-C；不可为 USB-A、HDMI、SD 卡读卡器、耳机插孔添加数量或位置。"
            "不得添加价格、续航、性能或跑分数字、处理器/内存/存储容量/刷新率等未提供规格，"
            "也不得声称亲身体验、推测兼容性或保证维修服务。"
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
    full_narration = " ".join(narration)
    if "预发布" not in narration[0] or "预发布" not in narration[-1]:
        raise ValueError("开场和结尾都必须说明这是预发布产品。")
    if not re.search(r"(?:不支持|不兼容|不提供).{0,8}(?:触控笔|Surface Pen)", full_narration):
        raise ValueError("口播稿必须说明触控屏不支持触控笔或 Surface Pen。")
    unverified_numeric_claim = re.compile(
        r"(?:¥|￥|\$|人民币\s*\d|\d+(?:\.\d+)?\s*(?:元|美元|小时|天|倍|%|％|GB|TB|GHz|MHz|TOPS|FPS|核|瓦|W|尼特))",
        re.IGNORECASE,
    )
    if unverified_numeric_claim.search(full_narration):
        raise ValueError("口播稿包含未核实的价格、续航或规格数字。")
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
