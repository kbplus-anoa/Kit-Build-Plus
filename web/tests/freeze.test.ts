import test from "node:test";
import assert from "node:assert/strict";

import { freezeRequested, paramsOf } from "../src/fx/freezeParams.ts";

test("没给参数：不冻结", () => {
  assert.equal(freezeRequested(paramsOf("")), false);
  assert.equal(freezeRequested(paramsOf("?device=mobile")), false);
  assert.equal(freezeRequested(paramsOf("?badge=1")), false);
});

test("fx=freeze 冻结，大小写与空白都认", () => {
  assert.equal(freezeRequested(paramsOf("?fx=freeze")), true);
  assert.equal(freezeRequested(paramsOf("?fx=FREEZE")), true);
  assert.equal(freezeRequested(paramsOf("?fx=%20freeze%20")), true);
});

test("fx 的其他取值不冻结", () => {
  assert.equal(freezeRequested(paramsOf("?fx=off")), false);
  assert.equal(freezeRequested(paramsOf("?fx=")), false);
});

test("veil=static 也认：临时测量架用过这个名字", () => {
  assert.equal(freezeRequested(paramsOf("?veil=static")), true);
  assert.equal(freezeRequested(paramsOf("?veil=freeze")), true);
  assert.equal(freezeRequested(paramsOf("?veil=none")), false);
});

test("两个参数并存：任一命中即冻结", () => {
  assert.equal(freezeRequested(paramsOf("?fx=off&veil=static")), true);
  assert.equal(freezeRequested(paramsOf("?fx=freeze&veil=none")), true);
  assert.equal(freezeRequested(paramsOf("?fx=off&veil=none")), false);
});

test("多余参数不影响判断", () => {
  assert.equal(freezeRequested(paramsOf("?device=mobile&fx=freeze&badge=1")), true);
});
