/** 五类差异的形状标记：形状说话，颜色不承担对错。 */
export type MarkKind =
  | "correct"
  | "lacking"
  | "excessive"
  | "leaving"
  | "reversed";

const PATHS: Record<MarkKind, React.ReactNode> = {
  correct: (
    <>
      <path d="M2.5 12h13" strokeWidth="1.6" />
      <path d="M12 7.5l4.5 4.5L12 16.5" strokeWidth="1.6" />
      <path d="M21 6.5v11" strokeWidth="2.4" />
    </>
  ),
  lacking: (
    <>
      <path d="M2.5 12h13" strokeWidth="1.6" strokeDasharray="3 3" />
      <path d="M12 7.5l4.5 4.5L12 16.5" strokeWidth="1.6" strokeDasharray="3 3" />
      <path d="M21 6.5v11" strokeWidth="2.4" strokeDasharray="2 2.4" />
    </>
  ),
  excessive: (
    <>
      <path d="M2.5 12h13" strokeWidth="3.2" />
      <path d="M12 7.5l4.5 4.5L12 16.5" strokeWidth="3.2" />
    </>
  ),
  leaving: (
    <>
      <path d="M2.5 12c2-4 4-4 6 0s4 4 6 0 4-4 5.5 0" strokeWidth="1.6" />
      <path d="M21 6.5v11" strokeWidth="2.4" />
    </>
  ),
  reversed: (
    <>
      <path d="M5 12h14" strokeWidth="1.6" />
      <path d="M15 7.5l4.5 4.5L15 16.5" strokeWidth="1.6" />
      <path d="M9 7.5L4.5 12 9 16.5" strokeWidth="1.6" />
    </>
  ),
};

export function Mark({ kind, size = 18 }: { kind: MarkKind; size?: number }) {
  return (
    <svg
      className="od-icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
      style={{ ["--od-icon-size" as string]: `${size}px` }}
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {PATHS[kind]}
    </svg>
  );
}