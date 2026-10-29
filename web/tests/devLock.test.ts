import test from "node:test";
import assert from "node:assert/strict";

import {
  DEV_PASSWORD, markLocked, markUnlocked, passOf, passwordOk, unlocked,
} from "../src/data/devLock.ts";

function memory() {
  const store = new Map();
  return {
    store,
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  };
}

test("密码对才开门", () => {
  assert.equal(passwordOk(DEV_PASSWORD), true);
  assert.equal(passwordOk("1234321"), true);
});

test("密码错、空、多余空白都开不了门", () => {
  assert.equal(passwordOk("123432"), false);
  assert.equal(passwordOk("12343211"), false);
  assert.equal(passwordOk(""), false);
  assert.equal(passwordOk(" 1234321"), false);
  assert.equal(passwordOk("1234321 "), false);
  assert.equal(passwordOk("abcd123"), false);
});

test("开门记下密码，落库时要带上它", () => {
  const store = memory();
  assert.equal(unlocked(store), false);
  assert.equal(passOf(store), "");
  markUnlocked(store, DEV_PASSWORD);
  assert.equal(unlocked(store), true);
  assert.equal(passOf(store), DEV_PASSWORD);
});

test("关上以后要重新输密码", () => {
  const store = memory();
  markUnlocked(store, DEV_PASSWORD);
  markLocked(store);
  assert.equal(unlocked(store), false);
  assert.equal(passOf(store), "");
});

test("只留了开门标记、没有密码：当成锁着", () => {
  const store = memory();
  store.setItem("kbp-dev-open", "1");
  assert.equal(unlocked(store), false);
});

test("存坏了就当锁着", () => {
  const broken = {
    getItem: () => {
      throw new Error("boom");
    },
    setItem: () => undefined,
    removeItem: () => undefined,
  };
  assert.equal(unlocked(broken), false);
  assert.equal(passOf(broken), "");
  assert.equal(unlocked(null), false);
});
