#!/usr/bin/env node
/**
 * 截图与测量架：headless Chrome 走 CDP，node 内置 fetch + WebSocket，不引任何依赖。
 *
 * 用法：cd web && node tools/shot.mjs <url> [--out 目录] [--w 宽] [--h 高] [--dpr 倍数]
 *
 * 收尾是本文件存在的主要理由：Chrome 会自己监督 --type=gpu-process 并在它崩掉后立刻
 * 重新拉起，只杀子进程等于触发重启。所以 spawn 时 detached 成独立进程组，任何出口
 * （正常结束、SIGINT、SIGTERM、未捕获异常、硬超时）都 process.kill(-pid, 'SIGKILL')
 * 杀整组；端口上不留东西，cgroup 里也不留孤儿。
 */

import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, isAbsolute, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const HARD_TIMEOUT_MS = 120000;
const PORT = Number(process.env.CDP_PORT || 9333);
const PROFILE = process.env.CDP_PROFILE || "/tmp/kbp-shot/profile";

function arg(name, fallback) {
  const at = process.argv.indexOf("--" + name);
  return at >= 0 && process.argv[at + 1] ? process.argv[at + 1] : fallback;
}

const url = process.argv[2];
if (!url || url.startsWith("--")) {
  console.error("用法: node tools/shot.mjs <url> [--out 目录] [--w 360] [--h 656] [--dpr 3]");
  process.exit(2);
}

const OUT = resolve(arg("out", resolve(HERE, "..", ".shots")));
const W = Number(arg("w", 360));
const H = Number(arg("h", 656));
const DPR = Number(arg("dpr", 3));

mkdirSync(OUT, { recursive: true });

/* ── Chrome：一个进程组，一个出口 ──────────────────────────────────── */

const chromeArgs = [
  "--headless=new",
  "--remote-debugging-port=" + PORT,
  "--user-data-dir=" + PROFILE,
  "--no-first-run",
  "--no-default-browser-check",
  "--hide-scrollbars",
  "--window-size=" + W + "," + H,
  "about:blank",
];

const chrome = spawn("google-chrome", chromeArgs, {
  stdio: ["ignore", "ignore", "pipe"],
  detached: true,
});

let stderrTail = "";
chrome.stderr.on("data", (chunk) => {
  stderrTail = (stderrTail + chunk.toString()).slice(-800);
});

let closed = false;

/** 杀掉整个进程组。pid 为负是关键：否则只杀 chrome 主进程，GPU 子进程会留下。 */
export function killGroup() {
  if (closed) return;
  closed = true;
  try {
    process.kill(-chrome.pid, "SIGKILL");
  } catch (err) {
    /* 组已经没了：正常出口 */
  }
}

function finish(code, message) {
  if (message) console.error(message);
  killGroup();
  process.exit(code);
}

process.on("exit", killGroup);
process.on("SIGINT", () => finish(130, "收到 SIGINT"));
process.on("SIGTERM", () => finish(143, "收到 SIGTERM"));
process.on("uncaughtException", (err) => finish(1, "未捕获异常: " + err.message));
process.on("unhandledRejection", (err) => finish(1, "未处理的 rejection: " + String(err)));

const hard = setTimeout(() => finish(124, "超过 " + HARD_TIMEOUT_MS + "ms 没跑完"), HARD_TIMEOUT_MS);

/* ── CDP ──────────────────────────────────────────────────────────── */

const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

async function target() {
  for (let i = 0; i < 150; i++) {
    try {
      const resp = await fetch("http://127.0.0.1:" + PORT + "/json/list");
      const list = await resp.json();
      const page = list.find((item) => item.type === "page");
      if (page) return page;
    } catch (err) {
      /* 还没起来 */
    }
    await sleep(100);
  }
  throw new Error("Chrome 没给页面: " + stderrTail.slice(-200));
}

let nextId = 0;
const pending = new Map();

function send(ws, method, params = {}) {
  const id = ++nextId;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((ok, fail) => pending.set(id, { ok, fail }));
}

async function evaluate(ws, expression) {
  const out = await send(ws, "Runtime.evaluate", {
    expression, returnByValue: true, awaitPromise: true,
  });
  if (out.exceptionDetails) throw new Error("页面里报错: " + JSON.stringify(out.exceptionDetails).slice(0, 300));
  return out.result.value;
}

async function main() {
  const page = await target();
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((ok, fail) => {
    ws.addEventListener("open", ok);
    ws.addEventListener("error", () => fail(new Error("连不上 CDP")));
  });

  const problems = [];
  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const { ok, fail } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) fail(new Error(JSON.stringify(msg.error)));
      else ok(msg.result);
      return;
    }
    if (msg.method === "Runtime.exceptionThrown") {
      problems.push(String(msg.params.exceptionDetails.text || "").slice(0, 200));
    }
  });

  await send(ws, "Page.enable");
  await send(ws, "Runtime.enable");
  await send(ws, "Emulation.setDeviceMetricsOverride", {
    width: W, height: H, deviceScaleFactor: DPR, mobile: W < 600,
    screenWidth: W, screenHeight: H,
  });
  await send(ws, "Page.navigate", { url });

  /* 等页面自己说画完了：fx 冻结时 window.KBPFx.frozen 为真 */
  for (let i = 0; i < 100; i++) {
    const ready = await evaluate(ws, "document.readyState === 'complete'");
    if (ready) break;
    await sleep(100);
  }
  await sleep(1200);

  const frozen = await evaluate(ws, "window.__kbpFrozen === true");
  if (frozen) {
    /* 冻结已接手：再给两帧让最后一个 still() 落到画布上 */
    await sleep(400);
  }

  const info = await evaluate(ws, `(() => ({
    dpr: window.devicePixelRatio,
    size: [window.innerWidth, window.innerHeight],
    canvases: [...document.querySelectorAll('canvas')].map((c) => ({
      id: c.id, buffer: [c.width, c.height],
    })),
    frozen: window.__kbpFrozen === true,
  }))()`);

  const shot = await send(ws, "Page.captureScreenshot", { format: "png", fromSurface: true });
  const file = resolve(OUT, "shot.png");
  writeFileSync(file, Buffer.from(shot.data, "base64"));

  console.log(JSON.stringify({ file, info, problems }));
  ws.close();
  clearTimeout(hard);
  finish(0);
}

main().catch((err) => finish(1, err.message));
