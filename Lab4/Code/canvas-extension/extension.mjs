// Adapted from the official extensions_manage canvas scaffold.
// This adapter only registers the Canvas. All business logic runs in Python.
import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
import { joinSession, createCanvas, CanvasError } from "@github/copilot-sdk/extension";

const config = JSON.parse(await readFile(new URL("./config.json", import.meta.url), "utf8"));
const panels = new Set();
let child;
let bridgePromise;

function bridge() {
    if (!bridgePromise) {
        bridgePromise = new Promise((resolve, reject) => {
            const worker = spawn(config.python, [config.bridge], { stdio: ["ignore", "pipe", "pipe"] });
            child = worker;
            let buffer = "";
            const timeout = setTimeout(() => {
                worker.kill("SIGTERM");
                reject(new CanvasError("python_bridge_timeout", "Python bridge did not start within 20 seconds"));
            }, 20000);
            worker.stderr.on("data", data => process.stderr.write(data));
            worker.once("error", error => {
                clearTimeout(timeout);
                if (child === worker) {
                    child = undefined;
                    bridgePromise = undefined;
                }
                reject(error);
            });
            worker.once("exit", code => {
                clearTimeout(timeout);
                if (child === worker) {
                    child = undefined;
                    bridgePromise = undefined;
                }
                reject(new CanvasError("python_bridge_exited", `Python bridge exited (${code})`));
            });
            worker.stdout.on("data", data => {
                buffer += data.toString();
                const newline = buffer.indexOf("\n");
                if (newline >= 0) {
                    clearTimeout(timeout);
                    worker.stdout.removeAllListeners("data");
                    try {
                        const result = JSON.parse(buffer.slice(0, newline));
                        const url = new URL(result.url);
                        if (url.hostname !== "127.0.0.1") throw new Error("Loopback required");
                        resolve(result.url);
                    } catch (error) {
                        worker.kill("SIGTERM");
                        reject(error);
                    }
                }
            });
        });
    }
    return bridgePromise;
}

function stop() {
    child?.kill("SIGTERM");
    child = undefined;
    bridgePromise = undefined;
}
process.once("exit", stop);
process.once("SIGTERM", () => { stop(); process.exit(0); });

await joinSession({
    canvases: [createCanvas({
        id: "hol-weekboard",
        displayName: "每周行动清单",
        description: "展示 Python 多 Agent 生成的虚构练习待办，并保存本地完成状态。",
        inputSchema: {
            type: "object",
            properties: { document_id: { const: "weekly-demo" } },
            required: ["document_id"], additionalProperties: false,
        },
        open: async ctx => {
            const url = await bridge();
            panels.add(ctx.instanceId);
            return { title: "每周行动清单 · 虚构练习数据", url };
        },
        actions: [{
            name: "complete",
            description: "设置一项本地待办的完成状态，不修改 Outlook。",
            inputSchema: {
                type: "object",
                properties: { id: { type: "string" }, done: { type: "boolean" } },
                required: ["id", "done"], additionalProperties: false,
            },
            handler: async ctx => {
                const url = await bridge();
                const response = await fetch(new URL("api/complete", url), {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-Workshop": "1" },
                    body: JSON.stringify(ctx.input),
                    signal: AbortSignal.timeout(10000),
                });
                const result = await response.json();
                if (!response.ok) throw new CanvasError("python_action_failed", result.error);
                return result;
            },
        }],
        onClose: async ctx => {
            panels.delete(ctx.instanceId);
            if (!panels.size) stop();
        },
    })],
});
