import { copyFile, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { marked } from "marked";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const out = path.join(root, "_site");
const labs = [
    { id: "lab-01", label: "Lab 01 · 楚河汉界", source: "Lab1/README.md", screenshots: [
        "03-generated-game.png", "04-legal-target.png", "05-first-move.png", "06-undo.png", "07-mobile.png",
    ] },
    { id: "lab-02", label: "Lab 02 · 两分钟产品短片", source: "Lab2/README.md", screenshots: [
        "04-video-opening.png", "05-video-ai.png", "06-video-display.png",
        "07-video-workflow.png", "08-video-ports.png", "09-video-repair.png",
    ] },
    { id: "lab-03", label: "Lab 03 · 经营观察室", source: "Lab3/README.md", screenshots: [
        "03-overview.png", "04-cloud-filter.png", "05-year-filter.png",
        "06-segment-view.png", "07-source-view.png",
    ] },
    { id: "lab-04", label: "Lab 04 · 每周工作罗盘", source: "Lab4/README.md", screenshots: [
        "03-training-capture.png", "04-weekly-board.png", "05-mail-evidence.png",
        "06-persistent-completion.png", "07-extension-runtime.png", "08-extension-renderer.png",
    ] },
];
const pages = [{ id: "home", label: "课程首页", source: "README.md", screenshots: [] }, ...labs];
const publicShots = new Map(labs.map(lab => [lab.id, new Set(lab.screenshots)]));

function escapeHtml(value) {
    return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function plainText(value) {
    return value.replace(/<[^>]*>/g, " ").replace(/&[a-z]+;/gi, " ")
        .replace(/\s+/g, " ").trim();
}

function sanitizeForPublic(markdown, id) {
    if (id === "home") {
        markdown = markdown.replace(
            /\*\*真实账户原图与输出仅存.*?验证。\*\*.*?(?=\n\n## )/s,
            "公开课程页只包含课程源码、虚构演示资料和经过筛选的教学截图。真实账户采集结果、本地验证日志与私人截图不会复制到 Pages 发布目录；原生自定义 Canvas 仍需在具备扩展管理能力的 App 会话中单独验收。"
        );
        markdown = markdown.replace(
            /\| 本人 Outlook 邮件与日历 \|.*\n/,
            "| 本人 Outlook 邮件与日历 | 个人授权流程仅供本地验收；公开课程页只展示虚构演示资料 |\n"
        );
        markdown = markdown.replace(
            /\| Lab 2 视频 \|.*\n/,
            "| Lab 2 视频 | edge-tts 中文女声与 HyperFrames CLI 导出的 1080×1920、30fps、120 秒 H.264 视频 |\n"
        );
        markdown = markdown.replace(
            /本机实测环境为 macOS、Python 3\.14\.7、Copilot CLI 1\.0\.103；其他系统仍需现场预检。/,
            "不同系统与工具版本可能有差异，开始前请运行版本预检命令。"
        );
        markdown = markdown.replace(
            /\*\*通过条件：\*\* `verification\/capabilities\.json` 中有 `gpt-6-luna`，/,
            "**通过条件：** 命令输出应确认模型能力包含 `gpt-6-luna`，"
        );
        markdown = markdown.replace(
            /`01-execution-record\.png` 是 \*\*真实 JSON 记录渲染后的浏览器截图\*\*.*?不能用运行记录替换。\n/,
            ""
        );
        markdown = markdown.replace(
            /本地 `verification\/` 报告及个人账户截图不会发布。/,
            "本机验收报告及个人账户截图不会发布。"
        );
    }
    if (id === "lab-01") {
        markdown = markdown.replace(
            /下面第一张是实际 App 新任务输入框，.*?模型执行记录。\n/,
            ""
        );
        markdown = markdown.replace(
            /App 原生新建会话与模型选择的实机配图仍在待补验收清单中。/,
            "App 的会话和模型选择界面可能随版本变化，请以当前界面为准。"
        );
    }
    if (id === "lab-02") {
        markdown = markdown.replace(
            /配图为实际 Plan 与 Autopilot 的 SDK 记录。步骤 3 另附后续原生验收会话的真实计划批准面板；不要把后续验收计划说成最初的分镜生成计划。\n/,
            ""
        );
        markdown = markdown.replace(
            /以下是本次制作中另外完成的\*\*原生验收计划\*\*：[\s\S]*?(?=^## 步骤 4)/m,
            "在 App 中审阅 Plan 输出后再批准；批准后仍需运行视频规格与完整解码检查。原生 App 截图属于本地验收材料，不属于公开演示。\n\n"
        );
    }
    if (id === "lab-03") {
        markdown = markdown.replace(
            /第一张是课程公共的\*\*真实 App 设置截图\*\*，.*?独立的 SDK 会话证据。\n/,
            ""
        );
    }
    if (id === "lab-04") {
        markdown = markdown.replace(
            /下图是实际三个独立模型会话和协议验证记录，不是 App 的设置界面。\n|下图是与 Lab 1 复用的同一次真实 App 公共设置截图，不把它当作三个 Agent 的执行证明。\n/g,
            ""
        );
        markdown = markdown.replace(
            /^\*\*虚构资料分支、独立 runtime 真实扩展和本人 Outlook 的选定资料匿名化流程均已运行。.*?\n/m,
            "**公开演示只使用虚构训练资料；真实账户步骤仅供学员在获授权的本地环境中操作。**\n"
        );
        markdown = markdown.replace(
            /^### 本次真实资料验收的具体范围\n[\s\S]*?(?=^## 本 Lab 的最终验收表)/m,
            "### 真实资料的公开边界\n个人邮箱、日历、账户身份和真实采集结果不包含在公开课程页中。公开流程只展示虚构训练资料；真实账户步骤仅供学员在自己的本地、经授权环境中操作。\n\n"
        );
        markdown = markdown.replace(
            /^\*\*检查：\*\* `verification\/canvas-rpc\.json`.*\n/m,
            "**检查：** 在当前 App 环境中分别确认 Canvas 能力发现、打开、动作调用和关闭；本机运行记录不属于公开课程内容。\n"
        );
        markdown = markdown.replace(
            /本次制作过程通过独立 Python SDK 会话显式请求扩展能力，已实际完成官方 scaffold、reload\/list\/inspect、open 和动作验证；证据为 `verification\/canvas-extension\.json`。\n/,
            "独立 SDK runtime 与 App 原生侧栏是不同验收面；本课程仅提供扩展示例和可复现的本地验证步骤。\n"
        );
        markdown = markdown.replace(
            /后续又创建了真实 App 验收会话，确认其中缺少 `extensions_manage` \/ `extensions_reload`，能力查询也没有 `hol-weekboard`。因此该原生会话未安装、未打开自定义 Canvas；macOS 权限已经开启，不应再把原因写成系统权限未授权。见 `verification\/native-ui\.json`。\n/,
            "如果当前 App 会话没有扩展管理工具或 Canvas 能力，请停止原生验收；不要把普通浏览器预览说成 App 原生侧栏。\n"
        );
        markdown = markdown.replace(
            /下图是与 Lab 1 复用的同一次真实 App 公共设置截图，不把它当作三个 Agent 的执行证明。\n/g,
            ""
        );
        markdown = markdown.replace(
            /^## 步骤 9 · 本人 Outlook 实操：这是需要授权的最后一段[\s\S]*$/m,
            "## 步骤 9 · 可选的本人 Outlook 实操\n\n真实账户实操仅供学员在本地、获授权的环境中进行，不属于公开演示数据。只处理本人明确选定的邮件与日历范围；登录信息、MFA、账户标识和原文不得写入提示词、截图或公开文件。执行模型分析前，先按组织政策核准并脱敏输入；拒绝授权或无法确认资料范围时，停止在虚构演示分支即可。\n\n公开课程页不包含任何真实邮件、日历事件、账户资料、采集结果或本地验收记录。\n"
        );
        markdown = markdown.replace(
            /^\| 本人 Outlook 邮件与日历 \|.*$/m,
            "| 本人 Outlook 邮件与日历 | 仅作为学员本地授权实操流程；公开演示使用虚构数据 | 个人资料不会进入公开页面 |"
        );
    }

    markdown = markdown.replace(
        /\[verification\/README\.md\]\(verification\/README\.md\)/g,
        "本地验证报告不属于公开发布内容"
    );
    markdown = markdown.replaceAll("../README.md", "../index.html");
    markdown = markdown.replaceAll("Lab1/README.md", "lab-01/index.html")
        .replaceAll("Lab2/README.md", "lab-02/index.html")
        .replaceAll("Lab3/README.md", "lab-03/index.html")
        .replaceAll("Lab4/README.md", "lab-04/index.html");

    markdown = markdown.replace(/!\[([^\]]*)\]\((screenshots\/[^)]+)\)/g, (whole, alt, href) => {
        const filename = path.posix.basename(href);
        if (id !== "home" && publicShots.get(id)?.has(filename)) {
            return `![${alt}](../assets/${id}/${filename})`;
        }
        return "";
    });
    return markdown;
}

function addHeadingIds(html) {
    const toc = [];
    const seen = new Map();
    const result = html.replace(/<h([1-6])>([\s\S]*?)<\/h\1>/g, (whole, levelText, inner) => {
        const level = Number(levelText);
        const title = plainText(inner);
        const base = title.toLocaleLowerCase().normalize("NFKC")
            .replace(/[^\p{L}\p{N}]+/gu, "-").replace(/^-|-$/g, "") || "section";
        const count = seen.get(base) || 0;
        seen.set(base, count + 1);
        const id = count ? `${base}-${count + 1}` : base;
        if (level === 2 || level === 3) toc.push({ id, title, level });
        return `<h${levelText} id="${escapeHtml(id)}">${inner}</h${levelText}>`;
    });
    return { html: result.replace(/<table>/g, '<div class="table-scroll"><table>')
        .replace(/<\/table>/g, "</table></div>"), toc };
}

function pageHref(page, current) {
    if (page.id === "home") return current.id === "home" ? "./index.html" : "../index.html";
    return current.id === "home" ? `./${page.id}/index.html` : `../${page.id}/index.html`;
}

function makeToc(toc, current) {
    if (!toc.length) return '<aside class="article-toc" aria-label="本页目录"><span class="article-toc-title">本页目录</span><p>首页概览</p></aside>';
    const links = toc.map(item =>
        `<a class="article-toc-link level-${item.level}" href="#${encodeURIComponent(item.id)}">${escapeHtml(item.title)}</a>`
    ).join("");
    return `<aside class="article-toc" aria-label="本页目录"><div class="article-toc-title">本页目录</div>${links}</aside>`;
}

function makeSidebar(current) {
    const links = pages.map((page, index) => {
        const active = page.id === current.id ? ' aria-current="page"' : "";
        const number = index === 0 ? "⌂" : String(index).padStart(2, "0");
        return `<a class="sidebar-link" href="${pageHref(page, current)}"${active}><span class="nav-number">${number}</span><span>${escapeHtml(page.label)}</span></a>`;
    }).join("");
    return `<aside class="sidebar" id="sidebar"><div class="sidebar-title">课程导航</div>${links}<div class="sidebar-note">先看目标，再运行代码；每一步都要核对实际输出。</div></aside>`;
}

function makePageNav(current) {
    const index = pages.findIndex(page => page.id === current.id);
    const previous = pages[index - 1];
    const next = pages[index + 1];
    if (!previous && !next) return "";
    const left = previous
        ? `<a class="page-nav-item" href="${pageHref(previous, current)}"><span>上一页</span><strong>${escapeHtml(previous.label)}</strong></a>`
        : '<span></span>';
    const right = next
        ? `<a class="page-nav-item next" href="${pageHref(next, current)}"><span>下一页</span><strong>${escapeHtml(next.label)}</strong></a>`
        : '<span></span>';
    return `<nav class="page-nav" aria-label="页面导航">${left}${right}</nav>`;
}

function renderPage(current, article, toc, searchIndex) {
    const homeHref = current.id === "home" ? "./index.html" : "../index.html";
    const rootPrefix = current.id === "home" ? "./" : "../";
    const breadcrumb = current.id === "home"
        ? '<span>课程首页</span>'
        : `<a href="${homeHref}">课程首页</a><span aria-hidden="true">/</span><span>${escapeHtml(current.label)}</span>`;
    const searchJson = JSON.stringify(searchIndex).replaceAll("<", "\\u003c");
    return `<!doctype html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="${escapeHtml(current.id === "home" ? "GitHub Copilot App 四个 Python 动手实验" : current.label)}">
<title>${escapeHtml(current.label)} · GitHub Copilot App 动手实验</title>
<link rel="stylesheet" href="${rootPrefix}assets/site.css">
</head>
<body>
<a class="skip-link" href="#main">跳到正文</a>
<header class="site-header"><div class="header-inner">
  <div class="header-left">
    <button class="menu-toggle" id="menu-toggle" aria-controls="sidebar" aria-expanded="false" aria-label="打开课程导航">☰</button>
    <a class="brand" href="${homeHref}"><span class="brand-mark">C</span><span><strong class="brand-name">GitHub Copilot App</strong><small class="brand-caption">动手实验 · Python 版</small></span></a>
  </div>
  <div class="header-actions">
    <div class="search-shell"><input id="site-search" type="search" placeholder="搜索课程…" aria-label="搜索课程" autocomplete="off"><div class="search-results" id="search-results" role="listbox"></div></div>
    <button class="header-button" id="theme-toggle" aria-label="切换深色主题" title="切换主题">◐</button>
  </div>
</div></header>
${makeSidebar(current)}
<div class="sidebar-overlay" id="sidebar-overlay"></div>
<div class="docs-layout"><div class="content-shell">
  <main class="main-content" id="main">
    <nav class="breadcrumbs" aria-label="面包屑">${breadcrumb}</nav>
    <div class="document-meta"><strong>${current.id === "home" ? "课程导览" : escapeHtml(current.label)}</strong><span>源码与公开演示资料</span></div>
    <article class="article">${article}</article>
    ${makePageNav(current)}
    <footer class="site-footer">此网站只发布课程源文件、虚构练习数据与筛选后的教学截图。个人账户资料、验证日志和本地环境文件不纳入 Pages。</footer>
  </main>
  ${makeToc(toc, current)}
</div></div>
<button class="scroll-top" id="scroll-top" aria-label="回到顶部" title="回到顶部">↑</button>
<script>window.HOL_PAGES=${searchJson};</script>
<script src="${rootPrefix}assets/site.js" defer></script>
</body></html>`;
}

async function ensureSafeOutput() {
    if (!out.startsWith(`${root}${path.sep}`)) throw new Error("Refusing to clean an output path outside the repository.");
    await rm(out, { recursive: true, force: true });
    await mkdir(path.join(out, "assets"), { recursive: true });
}

await ensureSafeOutput();
await copyFile(path.join(root, "site/site.css"), path.join(out, "assets/site.css"));
await copyFile(path.join(root, "site/site.js"), path.join(out, "assets/site.js"));
await writeFile(path.join(out, ".nojekyll"), "");

const searchIndex = [];
for (const page of pages) {
    let markdown = await readFile(path.join(root, page.source), "utf8");
    markdown = sanitizeForPublic(markdown, page.id);
    const rendered = marked.parse(markdown, { gfm: true });
    const { html, toc } = addHeadingIds(rendered);
    const title = plainText(html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/)?.[1] || page.label);
    const summary = plainText(html).slice(0, 220);
    searchIndex.push({ id: page.id, title, summary, text: plainText(html) });
    const destination = page.id === "home" ? path.join(out, "index.html")
        : path.join(out, page.id, "index.html");
    await mkdir(path.dirname(destination), { recursive: true });
    await writeFile(destination, renderPage(page, html, toc, searchIndex));
}

for (const page of pages) {
    const destination = page.id === "home" ? path.join(out, "index.html")
        : path.join(out, page.id, "index.html");
    const html = await readFile(destination, "utf8");
    await writeFile(destination, html.replace(
        /window\.HOL_PAGES=\[[\s\S]*?\];/,
        `window.HOL_PAGES=${JSON.stringify(searchIndex).replaceAll("<", "\\u003c")};`
    ));
}

for (const lab of labs) {
    const targetDir = path.join(out, "assets", lab.id);
    await mkdir(targetDir, { recursive: true });
    for (const screenshot of lab.screenshots) {
        const sourceLab = { "lab-01": "Lab1", "lab-02": "Lab2", "lab-03": "Lab3", "lab-04": "Lab4" }[lab.id];
        const source = path.join(root, sourceLab, "screenshots", screenshot);
        await copyFile(source, path.join(targetDir, screenshot));
    }
}

console.log(`Built ${pages.length} static pages in ${path.relative(root, out)}; private and unapproved evidence assets were not copied.`);
