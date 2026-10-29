import { createRoot } from "react-dom/client";

import "../../ui-share/styles/tokens.css";
import "../../ui-share/styles/base.css";
import "../../ui-share/styles/home.css";
import "../../ui-share/styles/report.css";
import "../../ui-share/styles/diagram.css";
import "../../ui-share/styles/subpage.css";
import "../../ui-share/styles/canvas.css";
import "../../ui-share/styles/load.css";
import "../../ui-share/styles/settings.css";
import "../../ui-share/styles/export.css";
import "../../ui-share/styles/batch.css";
import "../../ui-share/styles/device.css";
import { App } from "./App";
import { applyDevice } from "./data/device";

const mode = applyDevice();

if (new URLSearchParams(window.location.search).get("badge") === "1") {
  const badge = document.createElement("div");
  badge.textContent = "版式 " + (mode === "mobile" ? "手机版" : "电脑版");
  badge.style.cssText = [
    "position:fixed",
    "left:8px",
    "bottom:8px",
    "z-index:9999",
    "padding:2px 8px",
    "border-radius:999px",
    "background:rgba(0,0,0,.62)",
    "color:#fff",
    "font:11px/1.7 ui-monospace,monospace",
    "pointer-events:none",
  ].join(";");
  document.body.append(badge);
}

const root = document.getElementById("root");
if (!root) throw new Error("缺少 #root 挂载点");
createRoot(root).render(<App />);
