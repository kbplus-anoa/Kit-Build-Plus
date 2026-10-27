"""运行期裁 kit 的编排：题库命中、逐段进度、后台任务与结果封装。"""

import threading
import uuid
from datetime import datetime, timezone

import kbp.api.config_store
import kbp.api.deps
import kbp.contracts.triple
import kbp.extract.chat_client
import kbp.extract.discard_store
import kbp.extract.extract_service
import kbp.extract.quality
import kbp.extract.record_store
import kbp.extract.threshold_store
import kbp.extract.window
import kbp.ingest.materials
import kbp.kit.bank_store
import kbp.kit.freeze
import kbp.kit.kit_service
import kbp.kit.lock
import kbp.rebuild.usage
from kbp.api.schemas import ConceptOut, KitAutoOut, SignalOut

KEEP = 12

_JOBS: dict[str, dict] = {}
_LOCK = threading.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def to_vocab(book) -> kbp.contracts.triple.Vocab:
    return kbp.contracts.triple.Vocab(vocab_id=book.vocab_id,
                                      vocab_version=book.version,
                                      connections=tuple(book.connections))


def load_config():
    """当前抽取配置；未保存过时读 .env，仍是空配置。"""
    return kbp.api.config_store.load_config(kbp.api.deps.get_conn())


def preview(text: str) -> tuple[int, int]:
    """切段预报：抽之前先告诉前端这次要送几段。"""
    return (len(kbp.extract.window.split(text, load_config().max_chars)),
            len(text or ""))


def kit_out(kit, target, report=None, from_bank: bool = False) -> KitAutoOut:
    return KitAutoOut(
        map_version=kit.map_version,
        concepts=[ConceptOut(concept_id=c.concept_id, label=c.label)
                  for c in kit.concepts],
        connections=list(kit.connections),
        total_propositions=len(target.propositions),
        fingerprint=target.fingerprint, from_bank=from_bank,
        possibly_inaccurate=bool(report and report.possibly_inaccurate),
        message=report.message if report else "",
        signals=[SignalOut(name=s.name, label=s.label, value=s.value,
                           threshold=s.threshold, triggered=s.triggered)
                 for s in (report.signals if report else ())],
        calibrated=bool(report and report.calibrated),
        baseline_n=report.baseline_n if report else 0,
        baseline_source=report.baseline_source if report else "")


def auto(body, on_step=None) -> KitAutoOut:
    """先查题库命中即复用；未命中或要求重抽才抽取。"""
    conn = kbp.api.deps.get_conn()
    book = to_vocab(body.vocab)
    if not body.retry:
        entry = kbp.kit.kit_service.bank_find(conn, body.material_id,
                                              book.vocab_version)
        if entry is not None:
            target, kit = kbp.kit.kit_service.bank_kit(entry)
            ready(conn, body.material_id)
            return kit_out(kit, target, from_bank=True)
    return _extract(body, book, conn, on_step)


def _extract(body, book, conn, on_step) -> KitAutoOut:
    cfg = load_config()
    if on_step is None:
        details = kbp.extract.extract_service.extract_details(body.text, book, cfg)
    else:
        details = kbp.extract.extract_service.extract_details(
            body.text, book, cfg, on_step=on_step)
    target, kit, _ = kbp.kit.kit_service.freeze_to_bank(
        conn, body.material_id, details.result, now(), body.map_version,
        usage=kbp.rebuild.usage.SubmissionUsage(conn))
    _audit(conn, body, book, cfg, details, target)
    thresholds = kbp.extract.threshold_store.load(conn)
    report = kbp.extract.quality.assess(details.result, body.text, thresholds)
    ready(conn, body.material_id)
    return kit_out(kit, target, report)


def _audit(conn, body, book, cfg, details, target) -> None:
    digest = kbp.extract.extract_service.sha256(body.text)
    kbp.extract.discard_store.save(conn, digest, book, details.discards, now())
    batch_id = "auto-" + uuid.uuid4().hex[:16]
    kbp.extract.record_store.save(conn, kbp.extract.extract_service.record(
        details.result, batch_id, cfg, body.text, sections=details.sections,
        raw=details.raw, created_at=now(), discards=details.discards))
    kbp.extract.record_store.attach_map(conn, batch_id,
                                        target.map_version, target.fingerprint)


def ready(conn, material_id: int) -> None:
    with kbp.api.deps.db_lock():
        kbp.ingest.materials.mark_ready(conn, material_id)


def describe(exc: Exception) -> str:
    """后台任务的失败原因，与同步路由的文案保持一致。"""
    if isinstance(exc, (kbp.extract.extract_service.ExtractError,
                        kbp.extract.chat_client.MissingKey,
                        kbp.kit.lock.LockError)):
        return str(exc)
    if isinstance(exc, kbp.kit.freeze.FreezeError):
        return "抽出的图不足以成题: " + str(exc)
    if isinstance(exc, kbp.kit.bank_store.BankError):
        return "题库拒绝登记: " + str(exc)
    return "自动裁 kit 不可用: " + str(exc)


def _patch(job_id: str, **fields) -> None:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is not None:
            job.update(fields)


def _prune() -> None:
    with _LOCK:
        finished = [key for key, job in _JOBS.items()
                    if job["state"] != "running"]
        for key in finished[:-KEEP]:
            _JOBS.pop(key, None)


def start(body) -> dict:
    """开一个后台任务：抽取逐段推进，前端轮询取结果。"""
    job_id = uuid.uuid4().hex[:16]
    with _LOCK:
        _JOBS[job_id] = {"job_id": job_id, "state": "running", "segments": 0,
                         "done": 0, "error": "", "result": None,
                         "started_at": now(), "finished_at": ""}
    _prune()
    threading.Thread(target=_work, args=(job_id, body), daemon=True).start()
    return status(job_id)


def _work(job_id: str, body) -> None:
    def on_step(done: int, total: int) -> None:
        _patch(job_id, done=done, segments=total)

    try:
        data = auto(body, on_step=on_step).model_dump()
    except Exception as exc:  # noqa: BLE001 - 后台任务要把原因带回前端
        _patch(job_id, state="failed", error=describe(exc), finished_at=now())
        return
    snap = status(job_id) or {}
    total = int(snap.get("segments") or 0) or 1
    _patch(job_id, state="done", segments=total, done=total, result=data,
           finished_at=now())


def status(job_id: str) -> dict | None:
    with _LOCK:
        job = _JOBS.get(job_id)
        return dict(job) if job else None
