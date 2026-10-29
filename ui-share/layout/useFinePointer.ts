/**
 * 桌面级指针（鼠标）才用原生拖放。
 * 触屏没有拖放事件，手指一按就成了页面平移，所以触屏只留点击。
 */

import { useEffect, useState } from "react";

const QUERY = "(hover: hover) and (pointer: fine)";

export function useFinePointer(): boolean {
  const [fine, setFine] = useState(
    () => typeof window !== "undefined" && window.matchMedia(QUERY).matches,
  );
  useEffect(() => {
    const media = window.matchMedia(QUERY);
    const onChange = () => setFine(media.matches);
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);
  return fine;
}
