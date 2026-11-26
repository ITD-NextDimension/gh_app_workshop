"""Render real run records as labeled evidence pages, never as fake App UI."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE = """
body{margin:0;background:#f4f6fa;font:16px/1.8 system-ui,sans-serif;color:#243345}
main{max-width:1100px;margin:50px auto;padding:35px}
header{font-size:12px;letter-spacing:2px;color:#647a91}h1{font-size:38px;line-height:1.4}
.badge{background:#e5edf5;color:#45627f;padding:10px 18px;border-radius:8px}
section{background:white;padding:25px;border:1px solid #dde5ed;border-radius:12px;margin:24px 0}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.8 ui-monospace,monospace}
small{color:#7a8997}h2{font-size:18px}
"""


def render(lab, title, sections, filename="evidence.html"):
    body = f'<header>COPILOT HOL / {lab.upper()} / REAL EXECUTION RECORD</header><h1>{html.escape(title)}</h1>'
    body += '<div class="badge">真实运行记录的浏览器视图 · 不是 Copilot App 原生界面截图</div>'
    for heading, content in sections:
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False, indent=2)
        body += f'<section><h2>{html.escape(heading)}</h2><pre>{html.escape(content)}</pre></section>'
    body += '<small>本页是运行记录，不是 App 原生画面。真实 App 设置与计划批准另有截图；原生自定义 Canvas 仍待验收。私人原件不在本页展示。</small>'
    folder = ROOT / lab / "Code/output"
    folder.mkdir(exist_ok=True)
    target = folder / filename
    target.write_text(f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>{html.escape(title)}</title><style>{STYLE}</style><main>{body}</main></html>')
    return target


def trace_short(trace):
    return {key: trace[key] for key in ("role", "model", "mode", "session_id", "timestamp") if key in trace}


def build_all():
    generation = json.loads((ROOT / "Lab1/Code/generation.json").read_text())
    render("Lab1", "第一份作品：一次真实的 HTML 生成", [
        ("学员操作：新建会话，选择模式与模型", "App：Sessions → + → Open local folder → 课程根目录\n选择 Autopilot 与 GPT-6 Luna，限定只修改 Lab1/Code。\n本卡片是操作文字，不是该界面已经点击成功的证明。"),
        ("Python SDK 实际生成记录", trace_short(generation)),
        ("验收路径", "python Lab1/Code/generate.py\npython Lab1/Code/app.py\n浏览器：http://127.0.0.1:8011/generated.html\n32 个棋子、90 个交点、双人走棋、合法落点、悔棋和重新开始。"),
    ])
    story = json.loads((ROOT / "Lab2/Code/data/story.json").read_text())
    probe = json.loads((ROOT / "Lab2/Code/film/output/ffprobe.json").read_text())
    render("Lab2", "先规划，再执行：让官网成为竖屏短片", [
        ("Plan 阶段实际记录", {"trace": trace_short(story["plan_trace"]), "plan": story["plan"]}),
        ("Autopilot 阶段实际记录", {"trace": trace_short(story["trace"]), "execution": story["execution"]}),
        ("最终 MP4 实测规格", probe),
        ("来源与边界", "素材：Microsoft Surface Laptop Ultra 官网\n渲染：HyperFrames 0.8.171；不是用 Playwright 录屏冒充。\n声音：edge-tts zh-CN-XiaoxiaoNeural 普通话女声旁白；成片为 120 秒、1080×1920、30fps。\n官网产品图片不是开源授权素材。"),
    ])
    analysis = json.loads((ROOT / "Lab3/Code/output/analysis.json").read_text())
    render("Lab3", "一个 Agent，三条财报观察", [
        ("单 Agent 实际记录", trace_short(analysis["trace"])),
        ("Python 核对的官方数据（百万美元）", {
            "FY2025 Revenue": 281724, "FY2024 Revenue": 245122,
            "FY2025 Operating income": 128528, "FY2025 Net income": 101832,
            "Operating margin": "128528 / 281724 × 100 = 45.62%",
            "Fiscal year ended": "2025-06-30"}),
        ("模型实际解释", analysis["findings"]),
        ("边界", "Power BI 风格教学界面，不是 Power BI 产品。\n一个模型会话，没有工具可创建子 Agent。\n没有投资建议；所有筛选均为本地数据视图。"),
    ])
    plan = json.loads((ROOT / "Lab4/Code/output/plan.json").read_text())
    canvas = json.loads((ROOT / "verification/canvas-rpc.json").read_text())
    extension = json.loads((ROOT / "verification/canvas-extension.json").read_text())
    render("Lab4", "多 Agent 工作助理：已验证什么，未验证什么", [
        ("三个独立会话", [trace_short(t) for t in plan["traces"]]),
        ("Playwright 数据边界", "演示：3 封虚构邮件 + 3 个虚构日历事件，已从页面 DOM 读取并核对。\n演示时钟：2026-10-19 09:00 / Asia/Shanghai。\n真人分支：浏览器本人登录 → 限定范围读取 → 人工脱敏核对 → 明确允许模型分析。"),
        ("Python Canvas 的真实协议验证", canvas["checks"]),
        ("真实扩展验证", extension["checks"]),
        ("不能混淆的验收", "独立 SDK runtime 的真实插件已验证。\n真实 App 设置与计划批准已补拍，但原生验收会话缺少扩展管理工具，未打开自定义 Canvas。\n本人 Outlook 已登录，选定邮件与本周日历经本地匿名化后另行完成三 Agent 与页面验证；本页三个会话仍是虚构资料分支。"),
    ])
    render("Lab4", "真实 Canvas 插件：注册在运行时，业务在 Python", [
        ("验证范围", extension["scope"]),
        ("extensions_reload / list / inspect 实际结果", extension["runtime_status"]),
        ("运行时发现的声明", extension["discovery"]),
        ("真实通过项", extension["checks"]),
        ("仍需现场验收", "同一份扩展在 Copilot App 原生侧栏的展示和实机截图。\n真实 Outlook 的匿名化分支另见 outlook-live.json；私人原件不公开。"),
    ], filename="extension-evidence.html")
    live = json.loads((ROOT / "verification/outlook-live.json").read_text())
    render("Lab4", "已登录 Outlook：只公开检查项，不公开原件", [
        ("范围", live["scope"]),
        ("数据保护", {"original_content_sent_to_model": live["original_content_sent_to_model"],
                      "reviewer": live["reviewer"], "source_scope": live["source_scope"]}),
        ("实际通过项", live["checks"]),
        ("浏览器脚本错误", live["browser_errors"]),
        ("不是 App 原生截图", "本图是实测记录的浏览器呈现。原始邮件、日历和实际待办图片仅在 private，未嵌入公共讲义。"),
    ], filename="live-evidence.html")


if __name__ == "__main__":
    build_all()
