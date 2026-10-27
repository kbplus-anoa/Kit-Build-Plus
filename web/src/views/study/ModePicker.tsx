/** 模式选择：没选教材时整块锁住。 */
import { MODES } from "./copy";

export function ModePicker(props: {
  mode: "study" | "quiz" | null;
  locked: boolean;
  onMode: (mode: "study" | "quiz") => void;
}) {
  return (
    <div
      className={"mode-pick mode-pick__mask" + (props.locked ? " mode-pick--locked" : "")}
      aria-labelledby="rb-mode-title"
    >
      {MODES.map((item) => (
        <button
          key={item.id}
          type="button"
          className="mode-card"
          data-mode={item.id}
          aria-pressed={!props.locked && props.mode === item.id}
          tabIndex={props.locked ? -1 : 0}
          onClick={() => props.onMode(item.id)}
        >
          <span className="mode-card__name">{item.name}</span>
          <span className="mode-card__rule">{item.rule}</span>
          <span className="mode-card__tag">{item.tag}</span>
        </button>
      ))}
    </div>
  );
}
