"""Generate a working HTML game shell with GPT-6 Luna, retaining Python rules."""
import asyncio
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.agent import client, run_json

ROOT = Path(__file__).parent
SCHEMA = {"type": "object", "additionalProperties": False,
          "properties": {"html": {"type": "string"}}, "required": ["html"]}


async def main():
    prompt = (
        "为非计算机专业同事生成一个中国象棋游戏的完整 HTML 页面。输出 {html:string}。"
        "必须保留现成 Python 后端与 JS 规则接口，不能重新实现走棋规则。"
        "仅写 HTML，不要内联 JS、不使用 CDN。"
        "在 head 中引用 style.css，在 body 最后引用 app.js。"
        "保留以下唯一元素：id=board 的 div，id=status 的 span，id=error 的 p(role=alert)，"
        "id=undo 的 button(文字悔一步)，id=reset 的 button(文字重新开局)。"
        "使用中文文案、lang=zh-CN、viewport。参考以下已验证布局的 class 和结构，可改善文案。"
        "不要声称自己已经运行了测试。\n" + (ROOT / "index.html").read_text()
    )
    async with client() as copilot:
        result, trace = await run_json(copilot, "xiangqi-page-builder", prompt, SCHEMA)
    soup = BeautifulSoup(result["html"], "html.parser")
    for name in ("board", "status", "error", "undo", "reset"):
        if len(soup.select(f"#{name}")) != 1:
            raise ValueError(f"生成页面缺少唯一 #{name}，停止交付")
    if [s.get("src") for s in soup.find_all("script")] != ["app.js"]:
        raise ValueError("只允许现成 app.js")
    if soup.select_one('link[href="style.css"]') is None:
        raise ValueError("缺少本地样式")
    (ROOT / "generated.html").write_text(result["html"])
    (ROOT / "generation.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2))
    print("GPT-6 Luna 已生成 Code/generated.html；启动 app.py 后访问 /generated.html")


if __name__ == "__main__":
    asyncio.run(main())
