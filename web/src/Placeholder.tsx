/**
 * 占位壳：确认工程可跑、代理可达。
 * 页面设计由用户提供 HTML 原型后替换，本组件不含任何视觉决策。
 */

import { useEffect, useState } from "react";

import { api } from "./api/client";
import type { HealthOut } from "./types/api";

export function Placeholder() {
  const [health, setHealth] = useState<HealthOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p>后端未连通：{error}</p>;
  if (!health) return <p>连接后端中…</p>;
  return (
    <p>
      工程就绪 · 后端 {health.ok ? "正常" : "异常"} · 表数 {health.tables}
    </p>
  );
}
