/** 选中起点后从画布底部展开的连接词条，收起时先塌陷再摘掉。 */
import { useEffect, useState } from "react";

import { CONNECTORS } from "../../data/demo";

const CLOSE_MS = 280;

export function ConnectorChooser(props: {
  open: boolean;
  hint: string;
  armedConn: string | null;
  onPick: (word: string) => void;
}) {
  const [mounted, setMounted] = useState(false);
  const [lit, setLit] = useState(false);

  useEffect(() => {
    if (props.open) {
      setMounted(true);
      const frame = requestAnimationFrame(() => setLit(true));
      return () => cancelAnimationFrame(frame);
    }
    setLit(false);
    if (!mounted) return;
    const timer = window.setTimeout(() => setMounted(false), CLOSE_MS);
    return () => window.clearTimeout(timer);
  }, [props.open, mounted]);

  if (!mounted) return null;
  return (
    <div className={"rb__bar rb__chooser" + (lit ? " is-open" : "")}>
      <div className="rb__chooser__inner">
        <p className="rb__status">{props.hint}</p>
        <div className="rail__parts">
          {CONNECTORS.map((word) => {
            const armed = props.armedConn === word;
            return (
              <button
                key={word}
                type="button"
                className={"part part--conn" + (armed ? " is-armed" : "")}
                aria-pressed={armed}
                onClick={() => props.onPick(word)}
              >
                {word}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
