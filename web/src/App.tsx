/** 六个视图之间的唯一状态机：谁开着、带着哪份记录。视图常挂，动画类由路由挂在节点上。 */
import { useEffect, useState } from "react";

import { api } from "./api/client";
import type { Attempt } from "./data/attempt";
import type { Kit } from "./data/kit";
import { initAurora } from "./fx/init";
import { useAttempts } from "./hooks/useAttempts";
import { useKit } from "./hooks/useKit";
import { useRoute } from "./hooks/useRoute";
import { useTheme } from "./hooks/useTheme";
import type { MaterialOut } from "./types/api";
import { ExportView } from "./views/ExportView";
import { HistoryView } from "./views/HistoryView";
import { HomeView } from "./views/HomeView";
import { LoadView } from "./views/LoadView";
import { ReportView } from "./views/ReportView";
import { SettingsDialog } from "./views/SettingsDialog";
import { StudyView } from "./views/StudyView";

export function App() {
  const route = useRoute("home");
  const { theme, toggle } = useTheme(route.view);
  const [materials, setMaterials] = useState<MaterialOut[]>([]);
  const [current, setCurrent] = useState<Attempt | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [seed, setSeed] = useState<Attempt | null>(null);
  const [fresh, setFresh] = useState<number | null>(null);
  const [visit, setVisit] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const kitStore = useKit(nameOf);
  const attempts = useAttempts(nameOf);

  async function refreshMaterials() {
    try {
      const out = await api.materials();
      setMaterials(out.items);
    } catch {
      // 列表拉不到就先空着，上传入口照常可用
    }
  }

  function nameOf(materialId: number): string {
    const hit = materials.find((item) => item.material_id === materialId);
    return hit?.file_name ?? "教材 " + materialId;
  }

  function open(record: Attempt) {
    setCurrent(record);
    route.show("report");
  }

  function openSubmitted(materialId: number, seq: number) {
    const id = "srv-" + materialId + "-" + seq;
    void attempts.refreshRecords().then((list) => {
      const hit = list.find((item) => item.id === id);
      if (hit) open(hit);
      else void attempts.refreshRecords().then((again) => {
        const retry = again.find((item) => item.id === id);
        if (retry) open(retry);
      });
    });
    void attempts.refreshDrafts();
  }

  /** 测验已经交过：把库里那份报告直接打开，而不是把学生堵在 409。 */
  function openConflict(materialId: number) {
    void attempts.refreshRecords().then((list) => {
      const frozen = list.filter((item) => item.materialId === materialId && item.frozen);
      const latest = frozen[0];
      if (latest) {
        open(latest);
        return;
      }
      route.show("history");
    });
  }

  useEffect(() => {
    void initAurora();
    void refreshMaterials().then(() => attempts.refreshRecords());
    void attempts.refreshDrafts();
  }, []);

  function submitted(materialId: number, seq: number) {
    setSeed(null);
    openSubmitted(materialId, seq);
  }

  function start() {
    setSeed(null);
    setFresh(null);
    setVisit((value) => value + 1);
    route.show("study");
  }

  function revise(record: Attempt) {
    setSeed(record);
    setFresh(null);
    setVisit((value) => value + 1);
    route.show("study");
  }

  function upload(next: File) {
    setFile(next);
    route.show("load");
  }

  function loaded(next: Kit) {
    kitStore.adopt(next);
    setFile(null);
    setSeed(null);
    setFresh(next.materialId);
    setVisit((value) => value + 1);
    void refreshMaterials();
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
        onExport={() => route.show("export")}
        onSettings={() => setSettingsOpen(true)}
      />

      <SettingsDialog
        open={settingsOpen}
        onClose={() => {
          setSettingsOpen(false);
          void refreshMaterials();
        }}
      />

      <LoadView
        frame={route.frame("load")}
        file={file}
        onHome={route.home}
        onDone={loaded}
      />

      <StudyView
        key={(seed ? seed.id : "blank") + "-" + visit}
        frame={route.frame("study")}
        materials={materials}
        total={kitStore.kit?.total ?? 0}
        seed={seed}
        fresh={fresh}
        records={attempts.records}
        drafts={attempts.drafts}
        onHome={route.home}
        onFile={upload}
        onNeedKit={kitStore.needKit}
        onSubmitted={submitted}
        onConflict={openConflict}
        onDraftSaved={() => void attempts.refreshDrafts()}
        onOpenRecord={open}
        onUseVersion={kitStore.useVersion}
        onRetryBatch={kitStore.retryBatch}
      />

      {current ? (
        <ReportView
          frame={route.frame("report")}
          record={current}
          onHome={route.home}
          onRevise={revise}
        />
      ) : null}

      <HistoryView
        frame={route.frame("history")}
        records={attempts.records}
        onHome={route.home}
        onOpen={open}
      />

      <ExportView
        frame={route.frame("export")}
        materials={materials}
        onHome={route.home}
      />
    </>
  );
}
