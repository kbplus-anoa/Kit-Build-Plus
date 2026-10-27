/** 一条会自己退场的提示：连成了、连重了、删掉了。停 5.2 秒再淡出。 */
import { useEffect, useRef, useState } from "react";

import type { NoticeMsg } from "./useRebuild";

const HOLD_MS = 5200;

export function Notice(props: { notice: NoticeMsg | null }) {
  const [shown, setShown] = useState<NoticeMsg | null>(null);
  const [phase, setPhase] = useState<"hidden" | "in" | "leaving">("hidden");
  const hold = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (!props.notice) return;
    setShown(props.notice);
    setPhase("in");
    if (hold.current) window.clearTimeout(hold.current);
    hold.current = window.setTimeout(() => setPhase("leaving"), HOLD_MS);
    return () => {
      if (hold.current) window.clearTimeout(hold.current);
    };
  }, [props.notice]);

  const cls =
    "rb__notice" + (phase === "in" ? " is-in" : "") + (phase === "leaving" ? " is-leaving" : "");
  return (
    <div
      className={cls}
      hidden={phase === "hidden"}
      role="status"
      aria-live="polite"
      onAnimationEnd={(event) => {
        if (event.animationName !== "rb-notice-out") return;
        setPhase("hidden");
      }}
    >
      <span className="rb__notice__mark" aria-hidden="true">
        {shown?.mark ?? "·"}
      </span>
      <span>{shown?.text ?? ""}</span>
    </div>
  );
}
