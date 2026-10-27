/** 五个视图之间的唯一状态机：谁开着、带着哪份记录。视图常挂，动画类由路由挂在节点上。 */
import { useEffect, useState } from "react";

import { api } from "./api/client";
import type { Attempt } from "./data/attempt";
import { setKit, type Kit } from "./data/kit";
import { readRecords, writeRecords } from "./data/records";
import { PARTICIPANT_ID } from "./data/session";
import { VOCAB } from "./data/vocab";
import { initAurora } from "./fx/init";
import { useRoute } from "./hooks/useRoute";
import { useTheme } from "./hooks/useTheme";
import type { DraftOut, MaterialOut } from "./types/api";
import { HistoryView } from "./views/HistoryView";
import { HomeView } from "./views/HomeView";
import { LoadView } from "./views/LoadView";
import { ReportView } from "./views/ReportView";
import { SettingsDialog } from "./views/SettingsDialog";
import { StudyView } from "./views/StudyView";
import { attemptFromRecord, kitFrom } from "./views/study/attemptBuild";

export function App() {
  const route = useRoute("home");
  const { theme, toggle } = useTheme(route.view);
  const [materials, setMaterials] = useState<MaterialOut[]>([]);
  const [kit, setKitState] = useState<Kit | null>(null);
  const [records, setRecords] = useState<Attempt[]>(() => readRecords());
  const [drafts, setDrafts] = useState<DraftOut[]>([]);
  const [current, setCurrent] = useState<Attempt | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [seed, setSeed] = useState<Attempt | null>(null);
  const [visit, setVisit] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);

  async function refreshMaterials() {
    try {
      const out = await api.materials();
      setMaterials(out.items);
    } catch {
      // 列表拉不到就先空着，上传入口照常可用
    }
  }

  function adopt(next: Kit) {
    setKit(next);
    setKitState(next);
  }

  function nameOf(materialId: number): string {
    return materials.find((item) => item.material_id === materialId)?.file_name ?? "教材 " + materialId;
  }

  /** 记录只以后端为准；本地缓存只在拉不到时兜底。 */
  async function refreshRecords(): Promise<Attempt[]> {
    try {
      const out = await api.records(PARTICIPANT_ID);
      const remote = out.items.map((item) => attemptFromRecord(item, nameOf(item.material_id)));
      remote.sort((left, right) => right.when.localeCompare(left.when));
      setRecords(remote);
      return remote;
    } catch {
      return readRecords();
    }
  }

  async function refreshDrafts() {
    try {
      const out = await api.drafts(PARTICIPANT_ID);
      setDrafts(out.items);
    } catch {
      setDrafts([]);
    }
  }

  function openSubmitted(materialId: number, seq: number) {
    void refreshRecords().then((list) => {
      const id = "srv-" + materialId + "-" + seq;
      const hit = list.find((item) => item.id === id);
      if (hit) open(hit);
      else void refreshRecords().then((again) => {
        const retry = again.find((item) => item.id === id);
        if (retry) open(retry);
      });
    });
    void refreshDrafts();
  }

  /** 测验已经交过：把库里那份报告直接打开，而不是把学生堵在 409。 */
  function openConflict(materialId: number) {
    void refreshRecords().then((list) => {
      const frozen = list.filter((item) => item.materialId === materialId && item.frozen);
      const latest = frozen[0];
      if (latest) {
        open(latest);
        return;
      }
      route.show("history");
    });
  }

  /** 换一份教材进画布前先把它读回来；同一个词表版本会直接复用库里的目标图。 */
  async function needKit(materialId: number) {
    const text = await api.materialText(materialId);
    const auto = await api.kitAuto({
      material_id: materialId,
      text: text.text,
      vocab: VOCAB,
    });
    adopt(kitFrom(auto, materialId, text.file_name));
  }

  useEffect(() => {
    void initAurora();
    void refreshMaterials().then(() => refreshRecords());
    void refreshDrafts();
  }, []);

  useEffect(() => {
    writeRecords(records);
  }, [records]);

  function open(record: Attempt) {
    setCurrent(record);
    route.show("report");
  }

  function submitted(materialId: number, seq: number) {
    setSeed(null);
    openSubmitted(materialId, seq);
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

  function upload(next: File) {
    setFile(next);
    route.show("load");
  }

  function loaded(next: Kit) {
    adopt(next);
    setFile(null);
    setSeed(null);
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
        total={kit?.total ?? 0}
        seed={seed}
        records={records}
        drafts={drafts}
        onHome={route.home}
        onFile={upload}
        onNeedKit={needKit}
        onSubmitted={submitted}
        onConflict={openConflict}
        onDraftSaved={() => void refreshDrafts()}
        onOpenRecord={open}
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
        records={records}
        onHome={route.home}
        onOpen={open}
      />
    </>
  );
}
