/** 五个视图之间的唯一状态机：谁开着、带着哪份记录。视图常挂，动画类由路由挂在节点上。 */
import { useEffect, useState } from "react";

import { RECORDS, type Attempt } from "./data/demo";
import { initAurora } from "./fx/init";
import { useRoute } from "./hooks/useRoute";
import { useTheme } from "./hooks/useTheme";
import { HistoryView } from "./views/HistoryView";
import { HomeView } from "./views/HomeView";
import { LoadView } from "./views/LoadView";
import { ReportView } from "./views/ReportView";
import { StudyView } from "./views/StudyView";

export function App() {
  const route = useRoute("home");
  const { theme, toggle } = useTheme(route.view);
  const [docs, setDocs] = useState<string[]>(["认知心理学 · 记忆系统"]);
  const [records, setRecords] = useState<Attempt[]>(RECORDS);
  const [current, setCurrent] = useState<Attempt>(RECORDS[0]);
  const [pending, setPending] = useState("");
  const [seed, setSeed] = useState<Attempt | null>(null);
  const [visit, setVisit] = useState(0);

  useEffect(() => {
    void initAurora();
  }, []);

  function open(record: Attempt) {
    setCurrent(record);
    route.show("report");
  }

  function submit(record: Attempt, replacing: string | null) {
    setRecords((list) => [record, ...list.filter((item) => item.id !== replacing)]);
    setSeed(null);
    open(record);
  }

  function start() {
    setSeed(null);
    setVisit((value) => value + 1);
    route.show("study");
  }

  function revise(record: Attempt) {
    setSeed(record);
    setVisit((value) => value + 1);
    route.show("study");
  }

  function upload(name: string) {
    setPending(name);
    route.show("load");
  }

  function doneUpload(file: string) {
    const name = file.replace(/\.[^.]+$/, "") || "未命名教材";
    setDocs((list) => (list.includes(name) ? list : [name, ...list]));
    setPending("");
    setSeed(null);
    setVisit((value) => value + 1);
    route.show("study");
  }

  return (
    <>
      <div className="aurora" aria-hidden="true">
        <canvas className="aurora__gl" id="aurora-gl" />
      </div>

      <HomeView
        hidden={route.frame("home").hidden}
        inView={route.homeIn}
        out={route.homeOut}
        themeLabel={theme === "dark" ? "亮色" : "暗色"}
        onToggleTheme={toggle}
        onStudy={start}
        onHistory={() => route.show("history")}
      />

      <LoadView
        frame={route.frame("load")}
        file={pending}
        onHome={route.home}
        onDone={doneUpload}
      />

      <StudyView
        key={(seed ? seed.id : "blank") + "-" + visit}
        frame={route.frame("study")}
        docs={docs}
        seed={seed}
        records={records}
        onHome={route.home}
        onFile={upload}
        onSubmit={submit}
        onOpenRecord={open}
      />

      <ReportView
        frame={route.frame("report")}
        record={current}
        onHome={route.home}
        onRevise={revise}
      />

      <HistoryView
        frame={route.frame("history")}
        records={records}
        onHome={route.home}
        onOpen={open}
      />
    </>
  );
}
