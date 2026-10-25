"""Python entrypoint around the official HyperFrames CLI, not a substitute renderer."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent.resolve()
FILM = ROOT / "film"
VOICE = "zh-CN-XiaoxiaoNeural"
NARRATION = ROOT / "data/narration.txt"
VOICEOVER = FILM / "assets/narration.mp3"
HERO = "https://images.ctfassets.net/jy9s7k22hbg4/2FXwQdsQVLy6ZRGfq09eLX/39d4e78d90dcc0e476865ec371da68fb/SLU_Hero_Desktop_Poster__1_.jpg"


def prepare():
    assets = FILM / "assets"
    assets.mkdir(exist_ok=True)
    story = json.loads((ROOT / "data/story.json").read_text())["execution"]
    if len(story["scenes"]) != 6 or any(len(s) > 16 for s in story["scenes"]):
        raise ValueError("story.json 必须包含六个不超过16字的标题，请先运行 story.py")
    if len(story["narration"]) != 6:
        raise ValueError("story.json 必须包含六段口播稿，请先运行 story.py")
    if not NARRATION.is_file():
        NARRATION.write_text("\n\n".join(story["narration"]).strip() + "\n")
    index = FILM / "index.html"
    soup = BeautifulSoup(index.read_text(), "html.parser")
    for name, title in zip(
        ("opening", "ai", "display", "workflow", "connections", "repair"),
        story["scenes"],
        strict=True,
    ):
        element = soup.select_one("#" + name)
        if name in {"ai", "workflow", "repair"}:
            composition_soup = BeautifulSoup(
                (FILM / "compositions/chapter.html").read_text(), "html.parser"
            )
            composition_root = composition_soup.select_one("#root")
            composition_root["data-composition-id"] = f"chapter-{name}"
            values = json.loads(element["data-variable-values"])
            for variable, value in values.items():
                target = composition_soup.select_one(f'[data-var-text="{variable}"]')
                if target is None:
                    raise ValueError(f"章节模板缺少变量占位符：{variable}")
                target.string = value
                target.attrs.pop("data-var-text", None)
            composition_root.attrs.pop("data-composition-variables", None)
            script = composition_soup.select_one("script")
            script.string = script.string.replace(
                "window.__timelines.chapter=tl;",
                f'window.__timelines["chapter-{name}"]=tl;',
            )
            composition = FILM / f"compositions/chapter-{name}.html"
            composition.write_text(str(composition_soup))
            element["data-composition-src"] = f"compositions/chapter-{name}.html"
        else:
            values = json.loads(element.get("data-variable-values", "{}"))
            values["headline"] = title
            element["data-variable-values"] = json.dumps(values, ensure_ascii=False)
    index.write_text(str(soup))
    with urllib.request.urlopen(HERO, timeout=60) as response:
        image = response.read()
    (assets / "surface-hero.jpg").write_bytes(image)
    shutil.copyfile(ROOT / "node_modules/gsap/dist/gsap.min.js", assets / "gsap.min.js")
    for filename, url in {
        "NotoSansSC.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf",
        "OFL.txt": "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/OFL.txt",
    }.items():
        if not (assets / filename).exists():
            with urllib.request.urlopen(url, timeout=120) as response:
                (assets / filename).write_bytes(response.read())
    (assets / "source.json").write_text(json.dumps({
        "url": HERO, "page": "https://www.microsoft.com/en-us/surface/devices/surface-laptop-ultra",
        "sha256": hashlib.sha256(image).hexdigest(),
        "rights": "Microsoft product image; educational reference only. Not an open-source asset license.",
    }, indent=2))
    print("官网产品图已保存，未使用 AI 绘制的假产品图。")


def voice():
    if not NARRATION.is_file():
        raise FileNotFoundError("找不到 data/narration.txt，请先运行 story.py 和 video.py prepare。")
    VOICEOVER.parent.mkdir(exist_ok=True)
    subprocess.run([
        sys.executable, "-m", "edge_tts",
        "--file", str(NARRATION),
        "--voice", VOICE,
        "--rate=-5%",
        "--write-media", str(VOICEOVER),
        "--write-subtitles", str(FILM / "assets/narration.srt"),
    ], check=True)
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(VOICEOVER),
    ], check=True, capture_output=True, text=True)
    duration = float(json.loads(result.stdout)["format"]["duration"])
    if not 110 <= duration <= 120:
        raise ValueError(
            f"合成旁白为 {duration:.2f} 秒；应在110–120秒内以匹配2分钟视频。"
            "请调整 data/narration.txt 的篇幅后重新合成。"
        )
    soup = BeautifulSoup((FILM / "index.html").read_text(), "html.parser")
    audio = soup.select_one("#narration")
    audio["data-duration"] = f"{duration:.3f}"
    (FILM / "index.html").write_text(str(soup))
    print(f"已生成 {VOICE} 普通话女声：{VOICEOVER}（{duration:.2f} 秒）")


def run(*args):
    executable = shutil.which("npx")
    if not executable:
        raise RuntimeError("HyperFrames 的官方渲染器需要 Node.js 22+。Python 不替代它。")
    subprocess.run([executable, "--no-install", "hyperframes", *args], cwd=FILM, check=True)


def probe():
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,duration:format=duration",
        "-of", "json", str(FILM / "output/surface-ultra.mp4"),
    ], check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    assert (video["width"], video["height"]) == (1080, 1920), data
    assert abs(float(data["format"]["duration"]) - 120) < 0.1, data
    assert video["r_frame_rate"] == "30/1", data
    assert video["codec_name"] == "h264" and int(video["nb_frames"]) == 3600, data
    assert audio is not None, data
    audio_duration = float(audio.get("duration", data["format"]["duration"]))
    assert 110 <= audio_duration <= 120, data
    target = FILM / "output/ffprobe.json"
    target.write_text(json.dumps(data, indent=2))
    print(result.stdout)
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "voice", "check", "render", "probe"])
    command = parser.parse_args().command
    if command == "prepare":
        prepare()
    elif command == "voice":
        voice()
    elif command == "check":
        run("check", "--json")
    elif command == "render":
        (FILM / "output").mkdir(exist_ok=True)
        run("render", "--quality", "delivery", "--fps", "30", "--output", "output/surface-ultra.mp4")
        probe()
    else:
        probe()
