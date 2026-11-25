"""Prepare source-backed assets, synthesize narration, and run HyperFrames CLI."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

ROOT = Path(__file__).parent.resolve()
FILM = ROOT / "film"
RUN_ID = "2026-11-25"
STORY = ROOT / f"data/story-{RUN_ID}.json"
NARRATION = ROOT / f"data/narration-{RUN_ID}.txt"
VOICE = "zh-CN-XiaoxiaoNeural"
VOICEOVER = FILM / "assets" / f"narration-{RUN_ID}.mp3"
SUBTITLES = FILM / "assets" / f"narration-{RUN_ID}.srt"
OUTPUT = FILM / "output" / f"surface-ultra-{RUN_ID}.mp4"
PROBE_OUTPUT = FILM / "output" / f"ffprobe-{RUN_ID}.json"

PRODUCT_URL = "https://www.microsoft.com/en-us/surface/devices/surface-laptop-ultra"
SPECS_URL = "https://learn.microsoft.com/en-us/surface/tech-specs/surface-laptop-ultra-1stedition"
SOURCES = {
    "Microsoft Surface product page": PRODUCT_URL,
    "Microsoft Learn technical specifications": SPECS_URL,
}
ASSETS = {
    "surface-hero.jpg": "https://images.ctfassets.net/jy9s7k22hbg4/4KVqDIfm10HcC7B70bg5LR/5b81ac9612ddc0aad0b3c5c32f79d5b1/SLU_Hero_Mobile_Poster.jpg",
    "surface-ai-screen.jpg": "https://media.ffycdn.net/us/microsoft-consumer-brands/d/31db1a9c563645038227c1a4751f4b3f",
    "surface-3d.jpg": "https://media.ffycdn.net/us/microsoft-consumer-brands/d/19d7e2d00c774ca682c076e9a4ecdcc6",
    "surface-display.jpg": "https://images.ctfassets.net/jy9s7k22hbg4/6YHTTbvGNwpu7x9WOcBLXn/e3b63b4345ecf51f98ad4012259a0e21/SLU_402_Display_Afternoon_Poster__2___1_.jpg",
    "surface-ports.jpg": "https://media.ffycdn.net/us/microsoft-consumer-brands/d/23628a72eb7e4e33b2cae9f060234ff5",
    "surface-serviceability.jpg": "https://images.ctfassets.net/jy9s7k22hbg4/3DixSEZZgkEs60Sfd7upM/34f71bba22e8999bab7470a3b3bbb3e1/SLU_600_Serviceability_Poster__2_.jpg",
}
CHAPTER_IMAGES = {
    "ai": "assets/surface-ai-screen.jpg",
    "workflow": "assets/surface-display.jpg",
    "repair": "assets/surface-serviceability.jpg",
}
CHAPTER_SECONDARY_IMAGES = {"ai": "assets/surface-3d.jpg"}


def fetch(url, timeout=60):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Lab2SourceCheck/1.0)"})
    with urlopen(request, timeout=timeout) as response:
        return response.read(), response.geturl(), response.headers.get_content_type()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def prepare():
    assets_dir = FILM / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    story = json.loads(STORY.read_text(encoding="utf-8"))["execution"]
    if len(story["scenes"]) != 6 or any(len(scene) > 16 for scene in story["scenes"]):
        raise ValueError(f"{STORY.name} must contain exactly six titles of at most 16 characters.")
    if len(story["narration"]) != 6:
        raise ValueError(f"{STORY.name} must contain exactly six narration paragraphs.")
    NARRATION.write_text("\n\n".join(story["narration"]).strip() + "\n", encoding="utf-8")

    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_records = []
    for name, url in SOURCES.items():
        payload, final_url, content_type = fetch(url)
        if "html" not in content_type:
            raise ValueError(f"Expected an HTML source page at {url}, received {content_type}.")
        page_text = BeautifulSoup(payload, "html.parser").get_text(" ", strip=True)
        if "Surface Laptop Ultra" not in page_text:
            raise ValueError(f"Official page no longer identifies Surface Laptop Ultra: {url}")
        source_records.append({
            "name": name,
            "url": url,
            "final_url": final_url,
            "retrieved_at": retrieved_at,
            "sha256": sha256(payload),
        })

    asset_records = []
    for filename, url in ASSETS.items():
        payload, final_url, content_type = fetch(url)
        if not content_type.startswith("image/"):
            raise ValueError(f"Expected an official image at {url}, received {content_type}.")
        (assets_dir / filename).write_bytes(payload)
        asset_records.append({
            "file": filename,
            "url": url,
            "final_url": final_url,
            "content_type": content_type,
            "bytes": len(payload),
            "sha256": sha256(payload),
        })

    manifest = {
        "product": "Surface Laptop Ultra",
        "run_id": RUN_ID,
        "retrieved_at": retrieved_at,
        "sources": source_records,
        "assets": asset_records,
        "verified_claims": [
            "Microsoft positions Surface Laptop Ultra for local AI workloads and 3D graphics.",
            "15-inch touchscreen; touch interaction only, with no pen input or Surface Pen compatibility.",
            "Three USB-C ports, USB-A, HDMI, SD card reader, and 3.5 mm headphone jack.",
            "Published repair guides and upgradeable storage; service options vary by market and time.",
        ],
        "excluded_claims": ["price", "battery-life durations", "performance numbers or comparisons"],
        "rights": "Microsoft product imagery; no open license is implied. Confirm permission before external commercial publication.",
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (ROOT / "data/source.json").write_text(manifest_text, encoding="utf-8")
    (assets_dir / f"source-{RUN_ID}.json").write_text(manifest_text, encoding="utf-8")

    index = FILM / "index.html"
    soup = BeautifulSoup(index.read_text(encoding="utf-8"), "html.parser")
    for name, title in zip(
        ("opening", "ai", "display", "workflow", "connections", "repair"),
        story["scenes"],
        strict=True,
    ):
        element = soup.select_one("#" + name)
        if element is None:
            raise ValueError(f"film/index.html is missing the #{name} scene.")
        if name in {"ai", "workflow", "repair"}:
            chapter_document = BeautifulSoup(
                (FILM / "compositions/chapter.html").read_text(encoding="utf-8"),
                "html.parser",
            )
            chapter_template = chapter_document.find("template")
            if chapter_template is None:
                raise ValueError("chapter.html must contain a composition template.")
            composition_soup = BeautifulSoup(chapter_template.decode_contents(), "html.parser")
            composition_root = composition_soup.select_one("#root")
            if composition_root is None:
                raise ValueError("chapter.html template is missing its #root element.")
            composition_root["data-composition-id"] = f"chapter-{name}"
            values = json.loads(element["data-variable-values"])
            values["headline"] = title
            values["image"] = CHAPTER_IMAGES[name]
            if name in CHAPTER_SECONDARY_IMAGES:
                values["image2"] = CHAPTER_SECONDARY_IMAGES[name]
            else:
                secondary_image = composition_soup.select_one('[data-var-src="image2"]')
                if secondary_image is not None:
                    secondary_image.decompose()
            for variable, value in values.items():
                target = composition_soup.select_one(
                    f'[data-var-text="{variable}"], [data-var-src="{variable}"]'
                )
                if target is None:
                    raise ValueError(f"chapter.html is missing the {variable!r} placeholder.")
                if target.has_attr("data-var-text"):
                    target.string = value
                    target.attrs.pop("data-var-text", None)
                else:
                    target["src"] = value
                    target.attrs.pop("data-var-src", None)
            composition_root.attrs.pop("data-composition-variables", None)
            script = composition_soup.select_one("script")
            script.string = script.string.replace(
                "window.__timelines.chapter=tl;",
                f'window.__timelines["chapter-{name}"]=tl;',
            )
            chapter_template.clear()
            for child in list(composition_soup.contents):
                chapter_template.append(child.extract())
            composition = FILM / f"compositions/chapter-{name}.html"
            composition.write_text(str(chapter_document), encoding="utf-8")
            element["data-composition-src"] = f"compositions/chapter-{name}.html"
        else:
            values = json.loads(element.get("data-variable-values", "{}"))
            values["headline"] = title
            element["data-variable-values"] = json.dumps(values, ensure_ascii=False)
    audio = soup.select_one("#narration")
    if audio is None:
        raise ValueError("film/index.html is missing the narration audio track.")
    audio["src"] = f"assets/{VOICEOVER.name}"
    index.write_text(str(soup), encoding="utf-8")

    shutil.copyfile(ROOT / "node_modules/gsap/dist/gsap.min.js", assets_dir / "gsap.min.js")
    for filename, url in {
        "NotoSansSC.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf",
        "OFL.txt": "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/OFL.txt",
    }.items():
        if not (assets_dir / filename).exists():
            payload, _, _ = fetch(url, timeout=120)
            (assets_dir / filename).write_bytes(payload)
    print(f"Verified {len(source_records)} Microsoft sources and downloaded {len(asset_records)} official images.")


def voice():
    if not NARRATION.is_file():
        raise FileNotFoundError(f"Run video.py prepare first; missing {NARRATION}.")
    VOICEOVER.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        sys.executable, "-m", "edge_tts",
        "--file", str(NARRATION),
        "--voice", VOICE,
        "--rate=-5%",
        "--write-media", str(VOICEOVER),
        "--write-subtitles", str(SUBTITLES),
    ], check=True)
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(VOICEOVER),
    ], check=True, capture_output=True, text=True)
    duration = float(json.loads(result.stdout)["format"]["duration"])
    if not 110 <= duration <= 120:
        raise ValueError(
            f"Narration is {duration:.2f} seconds; target is 110–120 seconds. "
            f"Adjust {NARRATION.name} and rerun video.py voice."
        )
    soup = BeautifulSoup((FILM / "index.html").read_text(encoding="utf-8"), "html.parser")
    audio = soup.select_one("#narration")
    audio["data-duration"] = f"{duration:.3f}"
    (FILM / "index.html").write_text(str(soup), encoding="utf-8")
    print(f"Generated {VOICE} narration: {VOICEOVER} ({duration:.2f}s)")


def run(*args):
    executable = shutil.which("npx")
    if not executable:
        raise RuntimeError("HyperFrames CLI requires Node.js and npm/npx.")
    subprocess.run([executable, "--no-install", "hyperframes", *args], cwd=FILM, check=True)


def probe():
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,duration:format=duration",
        "-of", "json", str(OUTPUT),
    ], check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    video = next(stream for stream in data["streams"] if stream["codec_type"] == "video")
    audio = next((stream for stream in data["streams"] if stream["codec_type"] == "audio"), None)
    if (video["width"], video["height"]) != (1080, 1920):
        raise ValueError(f"Expected 1080x1920, received {video['width']}x{video['height']}.")
    if abs(float(data["format"]["duration"]) - 120) >= 0.1:
        raise ValueError(f"Expected 120 seconds, received {data['format']['duration']}.")
    if video["r_frame_rate"] != "30/1" or int(video["nb_frames"]) != 3600:
        raise ValueError("Expected 30fps and 3600 frames.")
    if video["codec_name"] != "h264":
        raise ValueError(f"Expected H.264, received {video['codec_name']}.")
    if audio is None:
        raise ValueError("The rendered MP4 has no audio stream.")
    audio_duration = float(audio.get("duration", data["format"]["duration"]))
    if not 110 <= audio_duration <= 120:
        raise ValueError(f"Expected 110–120 seconds of narration, received {audio_duration:.2f}s.")
    PROBE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PROBE_OUTPUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2))
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
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        run("render", "--quality", "delivery", "--fps", "30", "--output", str(OUTPUT.relative_to(FILM)))
        probe()
    else:
        probe()
