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
  timeout_s: 60,
  max_chars: 12000,
};

function reason(error: unknown): string {
  return error instanceof Error ? error.message : "请求失败";
}

export function SettingsDialog(props: Props) {
  const dialog = useRef<HTMLDialogElement | null>(null);
  const [config, setConfig] = useState<ConfigOut | null>(null);
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [maxChars, setMaxChars] = useState(String(FALLBACK.max_chars));
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
      setError("先填模型名，服务商给的那个 ID。");
      return;
    }
    if (!/^https?:\/\//.test(baseUrl.trim())) {
      setError("接口地址要以 http:// 或 https:// 开头，且不带 /v1。");
      return;
    }
    if (!Number.isFinite(chars) || chars <= 0) {
      setError("单次送入字数要是正整数。");
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
        上传后由这个接口读原文、抽概念、裁出目标图。任何 OpenAI 兼容
        <span className="mono"> /v1/chat/completions </span>
        服务都可以。
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
        <span className="settings__label">接口地址</span>
        <input
          className="settings__input"
          value={baseUrl}
          onChange={(event) => setBaseUrl(event.target.value)}
          placeholder="https://api.example.com"
          spellCheck={false}
        />
        <span className="settings__hint">根地址，不带 /v1，也不带末尾斜杠。</span>
      </label>

      <label className="settings__field">
        <span className="settings__label">单次送入字数</span>
        <input
          className="settings__input"
          value={maxChars}
          onChange={(event) => setMaxChars(event.target.value)}
          inputMode="numeric"
        />
        <span className="settings__hint">正文超出时按段切开分别送，默认 12000。</span>
      </label>

      <p className="settings__note">
        {keyLine}
        <br />
        密钥不写进库，也不经过浏览器；换密钥只需重启后端。
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
