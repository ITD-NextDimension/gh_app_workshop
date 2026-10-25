import assert from "node:assert/strict";
import { access, readFile, readdir } from "node:fs/promises";
import path from "node:path";
import test from "node:test";

const root = path.resolve(import.meta.dirname, "..");
const site = path.join(root, "_site");

test("build produces a home page and four lab pages", async () => {
    for (const page of ["index.html", "lab-01/index.html", "lab-02/index.html", "lab-03/index.html", "lab-04/index.html"]) {
        await access(path.join(site, page));
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
    const html = await readFile(path.join(site, "lab-04/index.html"), "utf8");
    assert.doesNotMatch(html, /20 个忙碌事件/);
    assert.doesNotMatch(html, /live-calendar-sunday\.png/);
    assert.doesNotMatch(html, /Code\/private\/|verification\/canvas-|verification\/native-ui/);
    assert.match(html, /不属于公开演示数据/);
});

test("only selected public demo screenshots are copied", async () => {
    const lab4Assets = await readdir(path.join(site, "assets/lab-04"));
    assert.ok(lab4Assets.includes("04-weekly-board.png"));
    assert.ok(lab4Assets.includes("08-extension-renderer.png"));
    assert.ok(!lab4Assets.includes("02-outlook-sign-in.png"));
    await assert.rejects(access(path.join(site, "Lab4/Code/private")));
});
