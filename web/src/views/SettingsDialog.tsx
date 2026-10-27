/** 抽取设置：填模型名与接口地址。密钥不进界面，只从后端进程的环境变量读。 */
import { useEffect, useRef, useState } from "react";

import { api } from "../api/client";
import type { ConfigOut } from "../types/api";

interface Props {
  open: boolean;
  onClose: () => void;
}

const FALLBACK = {
  provider: "openai_compatible",
  timeout_s: 120,
  max_chars: 12000,
};

const EFFORTS = [
  { value: "", label: "默认" },
  { value: "low", label: "低" },
  { value: "medium", label: "中" },
  { value: "high", label: "高" },
];

function reason(error: unknown): string {
  return error instanceof Error ? error.message : "请求失败";
}

export function SettingsDialog(props: Props) {
  const dialog = useRef<HTMLDialogElement | null>(null);
  const [config, setConfig] = useState<ConfigOut | null>(null);
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [maxChars, setMaxChars] = useState(String(FALLBACK.max_chars));
  const [effort, setEffort] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    if (props.open && !node.open) node.showModal();
    if (!props.open && node.open) node.close();
  }, [props.open]);

  useEffect(() => {
    if (!props.open) return;
    let live = true;
    setError("");
    setSaved(false);
    api
      .config()
      .then((loaded) => {
        if (!live) return;
        setConfig(loaded);
        setModel(loaded.model);
        setBaseUrl(loaded.base_url);
        setMaxChars(String(loaded.max_chars));
        setEffort(loaded.reasoning_effort);
      })
      .catch((failure: unknown) => {
        if (live) setError(reason(failure));
      });
    return () => {
      live = false;
    };
  }, [props.open]);

  async function save() {
    const chars = Number.parseInt(maxChars, 10);
    if (!model.trim()) {
      setError("请先填写模型名");
      return;
    }
    if (!/^https?:\/\//.test(baseUrl.trim())) {
      setError("接口地址要以 http:// 或 https:// 开头，且不带 /v1。");
      return;
    }
    if (!Number.isFinite(chars) || chars <= 0) {
      setError("单次送入字数须是正整数。");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const next = await api.saveConfig({
        provider: config?.provider ?? FALLBACK.provider,
        model: model.trim(),
        base_url: baseUrl.trim(),
        timeout_s: config?.timeout_s ?? FALLBACK.timeout_s,
        max_chars: chars,
        enabled: true,
        reasoning_effort: effort,
      });
      setConfig(next);
      setSaved(true);
    } catch (failure) {
      setError(reason(failure));
    } finally {
      setBusy(false);
    }
  }

  const keyLine = config
    ? config.has_key
      ? "密钥已配置。"
      : `还没配置密钥：启动后端时设置环境变量 ${config.key_env}。`
    : "正在读当前设置…";

  return (
    <dialog className="settings" ref={dialog} aria-labelledby="settings-title">
      <h2 className="settings__title" id="settings-title">抽取设置</h2>
      <p className="settings__lede">
        上传后由此接口读原文、裁组件、组目标图。任何 OpenAI 兼容
        <span className="mono"> /v1/chat/completions </span>
        api 都可以。
      </p>

      <label className="settings__field">
        <span className="settings__label">模型名</span>
        <input
          className="settings__input"
          value={model}
          onChange={(event) => setModel(event.target.value)}
          placeholder="服务商给的模型 ID"
          spellCheck={false}
        />
      </label>

      <label className="settings__field">
        <span className="settings__label">API 根地址 (OpenAI)	</span>
        <input
          className="settings__input"
          value={baseUrl}
          onChange={(event) => setBaseUrl(event.target.value)}
          placeholder="https://api.example.com"
          spellCheck={false}
        />
        <span className="settings__hint">如“https://api.deepseek.com”</span>
      </label>

      <label className="settings__field">
        <span className="settings__label">单次送入字数</span>
        <input
          className="settings__input"
          value={maxChars}
          onChange={(event) => setMaxChars(event.target.value)}
          inputMode="numeric"
        />
        <span className="settings__hint">若正文超出限制，则按段切分传入模型。默认 12000</span>
      </label>

      <label className="settings__field">
        <span className="settings__label">思考强度</span>
        <select
          className="settings__input"
          value={effort}
          onChange={(event) => setEffort(event.target.value)}
        >
          {EFFORTS.map((item) => (
            <option key={item.value} value={item.value}>{item.label}</option>
          ))}
        </select>
        <span className="settings__hint">
          越强越慢也越贵
        </span>
      </label>

      <p className="settings__note">
        {keyLine}
        也可以在 .env 配置。以该界面的配置优先
      </p>

      {config?.error ? <p className="settings__error">{config.error}</p> : null}
      {error ? <p className="settings__error">{error}</p> : null}
      {saved && !error ? <p className="settings__hint">已保存。</p> : null}

      <div className="settings__acts">
        <button type="button" className="btn btn--ghost" onClick={props.onClose}>
          关闭
        </button>
        <button type="button" className="btn btn--primary" onClick={save} disabled={busy}>
          {busy ? "保存中…" : "保存"}
        </button>
      </div>
    </dialog>
  );
}
