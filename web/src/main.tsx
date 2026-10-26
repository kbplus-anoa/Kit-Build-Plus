/**
 * 前端入口。当前只挂一个占位壳：页面设计由用户以 HTML 原型提供，
 * 本文件负责挂载与后续路由接入，不承担任何布局决策。
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { Placeholder } from "./Placeholder";

const root = document.getElementById("root");
if (!root) throw new Error("缺少 #root 挂载点");

createRoot(root).render(
  <StrictMode>
    <Placeholder />
  </StrictMode>,
);
