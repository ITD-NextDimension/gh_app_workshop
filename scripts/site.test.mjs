import assert from "node:assert/strict";
import { access, readFile, readdir } from "node:fs/promises";
import path from "node:path";
import test from "node:test";

const root = path.resolve(import.meta.dirname, "..");
const site = path.join(root, "_site");
const pagePaths = ["index.html", "lab-01/index.html", "lab-02/index.html", "lab-03/index.html", "lab-04/index.html"];

test("build produces a home page and four lab pages in both languages", async () => {
    for (const prefix of ["", "zh-TW/"]) {
        for (const page of pagePaths) await access(path.join(site, prefix, page));
    }
});

test("lab time boxes total three hours", async () => {
    const readmes = await Promise.all(["Lab1", "Lab2", "Lab3", "Lab4"].map(lab =>
        readFile(path.join(root, lab, "README.md"), "utf8")
    ));
    const minutes = readmes.map(readme => Number(readme.match(/预计 \*\*(\d+) 分钟\*\*/)?.[1]));
    assert.deepEqual(minutes, [35, 45, 45, 55]);
    assert.equal(minutes.reduce((total, value) => total + value, 0), 180);
});

test("pages include responsive navigation, search, theme and contents", async () => {
    const html = await readFile(path.join(site, "lab-04/index.html"), "utf8");
    assert.match(html, /id="sidebar"/);
    assert.match(html, /id="site-search"/);
    assert.match(html, /id="theme-toggle"/);
    assert.match(html, /class="article-toc"/);
    assert.match(html, /aria-current="page"/);
});

test("public page omits private live-account acceptance details", async () => {
    for (const prefix of ["", "zh-TW/"]) {
        const html = await readFile(path.join(site, prefix, "lab-04/index.html"), "utf8");
        assert.doesNotMatch(html, /20 [个個]忙碌事件/);
        assert.doesNotMatch(html, /live-calendar-sunday\.png/);
        assert.doesNotMatch(html, /Code\/private\/|verification\/canvas-|verification\/native-ui/);
        assert.match(html, prefix ? /不屬於公開演示資料/ : /不属于公开演示数据/);
    }
});

test("traditional READMEs retain all sections and executable commands", async () => {
    for (const directory of ["", "Lab1", "Lab2", "Lab3", "Lab4"]) {
        const original = await readFile(path.join(root, directory, "README.md"), "utf8");
        const traditional = await readFile(path.join(root, directory, "README.traditional.md"), "utf8");
        assert.equal(traditional.match(/^#{1,6} /gm).length, original.match(/^#{1,6} /gm).length);
        const commands = text => [...text.matchAll(/```(?:bash|powershell)\n([\s\S]*?)```/g)]
            .map(match => match[1].replace(/<guide [^>]+>/g, "<SDK path>"));
        assert.deepEqual(commands(traditional), commands(original), directory || "root");
        assert.match(traditional, /\[簡體中文\]\(README\.md\) \| \[繁體中文\]\(README\.traditional\.md\)/);
    }
});

test("language switches, navigation, assets and anchors resolve under a project Pages URL", async () => {
    for (const prefix of ["", "zh-TW/"]) {
        for (const page of pagePaths) {
            const relative = `${prefix}${page}`;
            const html = await readFile(path.join(site, relative), "utf8");
            const locale = prefix ? "zh-TW" : "zh-CN";
            assert.match(html, new RegExp(`<html lang="${locale}"`));
            const alternate = prefix ? "zh-CN" : "zh-TW";
            assert.match(html, new RegExp(`hreflang="${alternate}"`));
            if (prefix) {
                assert.match(html, /課程導航/);
                assert.match(html, /搜尋課程/);
                assert.match(html, /切換深色主題/);
            }
            const base = new URL(relative, "https://example.com/hol_ghc_app/");
            const search = JSON.parse(html.match(/window\.HOL_PAGES=(\[[\s\S]*?\]);/)[1]);
            assert.equal(search.length, 5);
            assert.ok(search.every(result => result.locale === locale));
            const links = [...html.matchAll(/(?:href|src)="([^"]+)"/g)].map(match => match[1]);
            links.push(...search.map(result => result.href));
            for (const link of links) {
                const url = new URL(link, base);
                if (url.origin !== base.origin) continue;
                assert.ok(url.pathname.startsWith("/hol_ghc_app/"), `${relative}: ${link}`);
                const target = path.join(site, decodeURIComponent(url.pathname.slice("/hol_ghc_app/".length)));
                await access(target);
                if (url.hash) {
                    const targetHtml = await readFile(target, "utf8");
                    assert.ok(targetHtml.includes(`id="${decodeURIComponent(url.hash.slice(1))}"`),
                        `${relative}: missing anchor ${link}`);
                }
            }
        }
    }
});

test("only selected public demo screenshots are copied", async () => {
    const lab4Assets = await readdir(path.join(site, "assets/lab-04"));
    assert.ok(lab4Assets.includes("04-weekly-board.png"));
    assert.ok(lab4Assets.includes("08-extension-renderer.png"));
    assert.ok(!lab4Assets.includes("02-outlook-sign-in.png"));
    await assert.rejects(access(path.join(site, "Lab4/Code/private")));
});
