import test from "node:test";
import assert from "node:assert/strict";

import { carried, onCanvas, CARRY_SLOP } from "../src/views/study/carry.ts";

const origin = { x: 100, y: 100 };
const rect = { left: 0, top: 0, width: 960, height: 540 };

test("手指没动：不算搬运，这一次是点击", () => {
  assert.equal(carried(origin, { x: 100, y: 100 }), false);
});

test("位移不到阈值：仍然算点击，免得手抖就搬走", () => {
  assert.equal(carried(origin, { x: 100 + CARRY_SLOP - 1, y: 100 }), false);
  assert.equal(carried(origin, { x: 104, y: 103 }), false);
});

test("位移到阈值：算搬运", () => {
  assert.equal(carried(origin, { x: 100 + CARRY_SLOP, y: 100 }), true);
  assert.equal(carried(origin, { x: 100, y: 100 - CARRY_SLOP - 1 }), true);
});

test("阈值可以给别的值", () => {
  assert.equal(carried(origin, { x: 103, y: 100 }, 4), false);
  assert.equal(carried(origin, { x: 104, y: 100 }, 4), true);
});

test("落在画布内：算落点", () => {
  assert.equal(onCanvas(rect, { x: 480, y: 270 }), true);
  assert.equal(onCanvas(rect, { x: 0, y: 0 }), true);
  assert.equal(onCanvas(rect, { x: 960, y: 540 }), true);
});

test("落在画布外：没有落点", () => {
  assert.equal(onCanvas(rect, { x: -1, y: 270 }), false);
  assert.equal(onCanvas(rect, { x: 961, y: 270 }), false);
  assert.equal(onCanvas(rect, { x: 480, y: -1 }), false);
  assert.equal(onCanvas(rect, { x: 480, y: 541 }), false);
});

test("画布还没铺开：没有落点", () => {
  assert.equal(onCanvas({ left: 0, top: 0, width: 0, height: 540 }, { x: 0, y: 0 }), false);
  assert.equal(onCanvas({ left: 0, top: 0, width: 960, height: 0 }, { x: 0, y: 0 }), false);
});

test("画布带偏移：按偏移后的实际位置判断", () => {
  const off = { left: 40, top: 120, width: 200, height: 100 };
  assert.equal(onCanvas(off, { x: 40, y: 120 }), true);
  assert.equal(onCanvas(off, { x: 240, y: 220 }), true);
  assert.equal(onCanvas(off, { x: 39, y: 120 }), false);
});
