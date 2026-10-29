import test from "node:test";
import assert from "node:assert/strict";

import { flowStart } from "../src/views/study/flowStart.ts";

const mats = (...ids: number[]) => ids.map((id) => ({ material_id: id, file_name: "m" + id }));

test("改报告：种子教材优先，不自动进画布", () => {
  const s = flowStart(mats(1, 2), 7, null);
  assert.deepEqual(s, { picked: 7, auto: false });
});

test("刚上传：选刚上传那份，并直接进画布", () => {
  const s = flowStart(mats(1, 2), null, 9);
  assert.deepEqual(s, { picked: 9, auto: true });
});

test("刚上传：列表还没刷新也要选中它", () => {
  const s = flowStart([], null, 9);
  assert.deepEqual(s, { picked: 9, auto: true });
});

test("平常进来：选列表第一份，停在选择教材处", () => {
  const s = flowStart(mats(3, 4), null, null);
  assert.deepEqual(s, { picked: 3, auto: false });
});

test("一份教材都没有：不选", () => {
  const s = flowStart([], null, null);
  assert.deepEqual(s, { picked: null, auto: false });
});
