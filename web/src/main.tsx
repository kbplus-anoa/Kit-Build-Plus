import { createRoot } from "react-dom/client";

import "../../ui-share/styles/tokens.css";
import "../../ui-share/styles/base.css";
import "../../ui-share/styles/home.css";
import "../../ui-share/styles/report.css";
import "../../ui-share/styles/diagram.css";
import "../../ui-share/styles/subpage.css";
import "../../ui-share/styles/canvas.css";
import "../../ui-share/styles/load.css";
import { App } from "./App";

const root = document.getElementById("root");
if (!root) throw new Error("缺少 #root 挂载点");
createRoot(root).render(<App />);
