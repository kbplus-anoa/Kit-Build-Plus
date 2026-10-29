# 临时 CDP 测量架把 Chrome 留成满载孤儿

## 现象

- headless Chrome 的 GPU 子进程 `--type=gpu-process --use-angle=swiftshader --enable-unsafe-swiftshader` 占 CPU 879%，累计约 21 核时，墙钟 2 小时 41 分。
- 父进程带 `--remote-debugging-port=9333 --user-data-dir=/tmp/aur/profbase --force-device-scale-factor=3 --window-size=360,656`；启动它的 node 早已退出，Chrome 被 `systemd --user` 收养成孤儿，仍在按 rAF 满帧渲染。
- 进程树里带 `--gpu-recent-crash-count=1`。

## 根因

三件事叠在一起才会满载，缺一件都到不了这个量级：

- `--use-angle=swiftshader` + `--enable-unsafe-swiftshader`：没有 GPU，全靠 CPU 软光栅。
- `--force-device-scale-factor=3`：片元数按面积放大到 9 倍，上面那件事的成本再乘 9。
- 首屏的 aurora 是 `requestAnimationFrame` 自循环，headless 里 `document.visibilityState` 永远是 visible，`visibilitychange` 一次都不触发，循环永不空闲。

清理不掉的第二个原因：`--type=gpu-process` 是浏览器主进程的子进程，杀掉它，主进程立刻重拉一个（`--gpu-recent-crash-count` 就是这么累加出来的）。只杀 GPU 子进程等于没杀。

第三个原因：当时以为地址栏有 `?veil=static&grain=0` 这个开关，仓库里从来没有实现过——只有 `?device=` 与 `?badge=1`。测量架没法让页面停下来，只能等它自己跑完，也就没有收尾的时机。

## 复现

用旧办法开一版测量架，让它跑十几分钟，再杀掉 node：

```
node <旧测量脚本> http://127.0.0.1:5173/ --dpr 3 --w 360 --h 656
```

```
ps -eo pid,pcpu,etime,args | grep -- '--type=gpu-process' | grep -v grep
```

CPU 会一直顶在高位；`kill <gpu pid>` 之后几秒内又出现新的 GPU 子进程，父进程的 `--gpu-recent-crash-count` 加一。

## 修复

- `web/src/fx/freezeParams.ts`：`freezeRequested()` 认 `?fx=freeze|static|still` 与 `?veil=freeze|static|still`，两边任一命中即冻结。
- `web/src/fx/freeze.js`：命中时置 `window.__kbpFrozen`，给测量架读。
- `aurora.js` / `globe.js` / `loadglobe.js`：冻结走各自既有的静帧路径（`still()`、装配完成的那一帧、`stopTicker()` 之后的那一帧），不另写渲染路径；同时暴露 `freeze()` 供外部调用。正常浏览与 prefers-reduced-motion 分支不变。
- `web/tools/shot.mjs`：只有内置 `fetch` 与 `WebSocket`，不引 puppeteer / playwright；Chrome 用 `spawn(..., { detached: true })` 进独立进程组，`SIGINT`、`SIGTERM`、`exit`、`uncaughtException`、`unhandledRejection`、硬超时全部走 `process.kill(-chrome.pid, "SIGKILL")` 整组带走。

## 验收

- `node tools/shot.mjs 'http://127.0.0.1:5173/?fx=freeze&device=desktop' --dpr 3` 回包 `frozen: true`、`problems` 为空。
- 同一地址连跑两次，截图逐像素比对无差异（冻结停在确定的一帧）；去掉 `fx=freeze` 再连跑两次，差异明显。
- 脚本退出后 `pgrep -af 'remote-debugging-port=9333'` 无输出，GPU 子进程一并消失。
- 不开冻结参数时页面照常动，`prefers-reduced-motion` 的静帧行为不变。
- `npm run typecheck`、`npm run build`、`.venv/bin/python -m pytest` 退出码全为 0。

## 不做

- 不靠杀 `--type=gpu-process` 收尾，会被主进程重新拉起。
- 不把 `visibilitychange` 当兜底，headless 里它不触发。
- 不用 `--single-process` 或 `--no-sandbox` 绕开。
- 不顺手调 fx 的视觉效果。
