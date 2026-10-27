/** 差异图五种笔迹各自的箭头。 */
import type { MarkKind } from "../atoms/Mark";

const KINDS: MarkKind[] = ["correct", "lacking", "excessive", "leaving", "reversed"];

export function DiffMarkerDefs() {
  return (
    <defs>
      {KINDS.map((kind) => (
        <marker
          key={kind}
          id={`diff-arrow-${kind}`}
          className={`arrow--${kind}`}
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth="5"
          markerHeight="5"
          orient="auto-start-reverse"
          markerUnits="strokeWidth"
        >
          <path d="M0 0 L10 5 L0 10 z" fill="currentColor" />
        </marker>
      ))}
    </defs>
  );
}
