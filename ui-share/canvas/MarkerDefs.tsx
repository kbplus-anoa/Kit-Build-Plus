/** 画布箭头：一条路径，按线的颜色走，主题切换时不用重画。 */
export function MarkerDefs() {
  return (
    <defs>
      <marker
        id="rb-arrow"
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
    </defs>
  );
}
