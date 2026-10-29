import test from "node:test";
import assert from "node:assert/strict";

import {
  parseFlag, readFlag, writeFlag, devOn, setDev, toggleDev, subscribeDev,
} from "../src/data/devMode.ts";

function memory() {
  const store = new Map();
  return {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  };
}

test("只有 1 算开着", () => {
  assert.equal(parseFlag("1"), true);
  assert.equal(parseFlag("0"), false);
  assert.equal(parseFlag("true"), false);
  assert.equal(parseFlag(""), false);
  assert.equal(parseFlag(null), false);
});

test("写进去再读回来一致", () => {
  const store = memory();
  writeFlag(store, true);
  assert.equal(readFlag(store), true);
  writeFlag(store, false);
  assert.equal(readFlag(store), false);
});

test("没存过就是关着", () => {
  assert.equal(readFlag(memory()), false);
});

test("开关会通知订阅者，退订后不再通知", () => {
  const seen = [];
  const off = subscribeDev(() => seen.push(devOn()));
  setDev(true);
  setDev(false);
  off();
  setDev(true);
  assert.deepEqual(seen, [true, false]);
  setDev(false);
});

test("一次切换把状态翻过来", () => {
  setDev(false);
  toggleDev();
  assert.equal(devOn(), true);
  toggleDev();
  assert.equal(devOn(), false);
});
