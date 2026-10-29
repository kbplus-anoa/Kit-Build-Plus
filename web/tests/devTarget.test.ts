import test from "node:test";
import assert from "node:assert/strict";

import { applyOverlay } from "../src/data/devKit.ts";
import {
  addTargetEdge, pruneTarget, removeTargetEdge, replaceTargetEdge, targetOf,
} from "../src/data/devTarget.ts";

const kit = {
  materialId: 3, material: "记忆.pdf", mapVersion: "v1",
  concepts: [{ id: "c1", label: "记忆" }, { id: "c2", label: "感觉记忆" }],
  connections: ["包括", "导致"],
  target: [{ from: "c1", conn: "包括", to: "c2" }],
  total: 1,
};

const ids = ["c1", "c2"];
const words = ["包括", "导致"];
const t0 = () => [{ from: "c1", conn: "包括", to: "c2" }];

test("targetOf 取 kit 的目标图，没带就是空", () => {
  assert.deepEqual(targetOf(kit), t0());
  assert.deepEqual(targetOf({ ...kit, target: undefined }), []);
});

test("加一条目标命题：三段都在才收，重复不收", () => {
  const added = addTargetEdge(t0(), ids, words, { from: "c2", conn: "导致", to: "c1" });
  assert.deepEqual(added, [
    { from: "c1", conn: "包括", to: "c2" },
    { from: "c2", conn: "导致", to: "c1" },
  ]);
  assert.equal(addTargetEdge(t0(), ids, words, { from: "c1", conn: "包括", to: "c2" }), null);
  assert.equal(addTargetEdge(t0(), ids, words, { from: "zz", conn: "包括", to: "c2" }), null);
  assert.equal(addTargetEdge(t0(), ids, words, { from: "c1", conn: "没有", to: "c2" }), null);
  assert.equal(addTargetEdge(t0(), ids, words, { from: "c1", conn: "包括", to: "c1" }), null);
});

test("删一条目标命题：按三段认", () => {
  const edges = [
    { from: "c1", conn: "包括", to: "c2" },
    { from: "c2", conn: "导致", to: "c1" },
  ];
  assert.deepEqual(removeTargetEdge(edges, { from: "c1", conn: "包括", to: "c2" }), [
    { from: "c2", conn: "导致", to: "c1" },
  ]);
  assert.deepEqual(removeTargetEdge(edges, { from: "x", conn: "包括", to: "c2" }), edges);
});

test("改一条目标命题：换概念、换连接词、整个换成别的三段", () => {
  const edges = [
    { from: "c1", conn: "包括", to: "c2" },
    { from: "c2", conn: "导致", to: "c1" },
  ];
  const old = edges[0];
  assert.deepEqual(replaceTargetEdge(edges, ids, words, old, { from: "c1", conn: "导致", to: "c2" }), [
    { from: "c1", conn: "导致", to: "c2" },
    { from: "c2", conn: "导致", to: "c1" },
  ]);
  assert.deepEqual(replaceTargetEdge(edges, ids, words, old, { from: "c2", conn: "包括", to: "c2" }), null);
});

test("改一条目标命题：换完不成立或撞上别的命题都不收", () => {
  const edges = [
    { from: "c1", conn: "包括", to: "c2" },
    { from: "c2", conn: "导致", to: "c1" },
  ];
  const old = edges[0];
  assert.equal(replaceTargetEdge(edges, ids, words, old, { from: "zz", conn: "包括", to: "c2" }), null);
  assert.equal(replaceTargetEdge(edges, ids, words, old, { from: "c1", conn: "没有", to: "c2" }), null);
  assert.equal(replaceTargetEdge(edges, ids, words, old, { from: "c1", conn: "包括", to: "c1" }), null);
  assert.equal(replaceTargetEdge(edges, ids, words, old, edges[1]), null);
});

test("改一条目标命题：没改就原样返回那一份", () => {
  const edges = t0();
  assert.equal(replaceTargetEdge(edges, ids, words, edges[0], { ...edges[0] }), edges);
});

test("概念删掉后，目标图里用到它的命题也撤下", () => {
  const edges = [
    { from: "c1", conn: "包括", to: "c2" },
    { from: "c2", conn: "导致", to: "c1" },
  ];
  assert.deepEqual(pruneTarget(edges, ["c2"], ["包括", "导致"]), []);
  assert.deepEqual(pruneTarget(edges, ["c1", "c2"], ["导致"]), [
    { from: "c2", conn: "导致", to: "c1" },
  ]);
});

test("叠层套回 kit 时目标图用的是叠层那份", () => {
  const out = applyOverlay(kit, {
    concepts: kit.concepts, connections: kit.connections,
    target: [],
  });
  assert.deepEqual(out.target, []);
  assert.deepEqual(targetOf(out), []);
});
