import test from "node:test";
import assert from "node:assert/strict";

import {
  applyOverlay, addConcept, renameConcept, removeConcept,
  addConnector, renameConnector, removeConnector, pruneEdges, prunePlaced,
} from "../src/data/devKit.ts";

function kit(over = {}) {
  return {
    materialId: 3,
    material: "记忆.pdf",
    mapVersion: "v1",
    concepts: [{ id: "c1", label: "记忆" }, { id: "c2", label: "感觉记忆" }],
    connections: ["包括", "导致"],
    target: [{ from: "c1", conn: "包括", to: "c2" }],
    total: 1,
    ...over,
  };
}

const ids = (list) => list.map((item) => item.id);
const labels = (list) => list.map((item) => item.label);

test("没有叠层：原样返回", () => {
  const base = kit();
  const out = applyOverlay(base, null);
  assert.equal(out, base);
  assert.deepEqual(out.concepts, base.concepts);
});

test("叠层把概念、连接词与目标图整份换掉，教材与版本不动", () => {
  const out = applyOverlay(kit(), {
    concepts: [{ id: "x", label: "新" }],
    connections: ["变成"],
    target: [],
  });
  assert.deepEqual(ids(out.concepts), ["x"]);
  assert.deepEqual(out.connections, ["变成"]);
  assert.deepEqual(out.target, []);
  assert.equal(out.materialId, 3);
  assert.equal(out.mapVersion, "v1");
});

test("叠层里的目标图就是那一刻的目标图，不吃 kit 带来的那份", () => {
  const out = applyOverlay(kit(), {
    concepts: kit().concepts, connections: kit().connections,
    target: [{ from: "c2", conn: "导致", to: "c1" }],
  });
  assert.deepEqual(out.target, [{ from: "c2", conn: "导致", to: "c1" }]);
});

test("新增概念：去空白、给不撞车的 id", () => {
  const out = addConcept(kit().concepts, "  长时记忆 ");
  assert.equal(out.list.length, 3);
  assert.equal(out.list[2].label, "长时记忆");
  assert.equal(ids(out.list).filter((id) => id === out.list[2].id).length, 1);
});

test("新增概念：空白与重名都不收", () => {
  assert.equal(addConcept(kit().concepts, "   "), null);
  assert.equal(addConcept(kit().concepts, "记忆"), null);
});

test("新增概念：id 不和已有的撞", () => {
  const many = [{ id: "c1", label: "甲" }, { id: "dev-1", label: "乙" }];
  const out = addConcept(many, "丙");
  assert.equal(ids(out.list).includes("dev-1"), true);
  assert.equal(new Set(ids(out.list)).size, 3);
});

test("改名：只动那一条", () => {
  const out = renameConcept(kit().concepts, "c1", " 短时记忆 ");
  assert.deepEqual(labels(out), ["短时记忆", "感觉记忆"]);
  assert.deepEqual(ids(out), ["c1", "c2"]);
});

test("改名：空白不收、找不到 id 原样返回", () => {
  const before = kit().concepts;
  assert.deepEqual(renameConcept(before, "c1", "  "), before);
  assert.deepEqual(renameConcept(before, "zz", "新的"), before);
});

test("改名：撞上别的概念的字面也不收", () => {
  const before = kit().concepts;
  assert.deepEqual(renameConcept(before, "c1", "感觉记忆"), before);
});

test("删概念：只去掉那一条", () => {
  assert.deepEqual(ids(removeConcept(kit().concepts, "c1")), ["c2"]);
  assert.deepEqual(ids(removeConcept(kit().concepts, "zz")), ["c1", "c2"]);
});

test("新增连接词：去空白、重名不收", () => {
  assert.deepEqual(addConnector(["包括"], " 导致 "), ["包括", "导致"]);
  assert.equal(addConnector(["包括"], "包括"), null);
  assert.equal(addConnector(["包括"], "  "), null);
});

test("连接词改名与删除", () => {
  assert.deepEqual(renameConnector(["包括", "导致"], "包括", "包含"), ["包含", "导致"]);
  assert.deepEqual(renameConnector(["包括"], "包括", "包含"), ["包含"]);
  assert.deepEqual(renameConnector(["包括"], "没有", "包含"), ["包括"]);
  assert.deepEqual(renameConnector(["包括", "导致"], "包括", "导致"), ["包括", "导致"]);
  assert.deepEqual(removeConnector(["包括", "导致"], "包括"), ["导致"]);
});

const edges = () => ([
  { from: "c1", conn: "包括", to: "c2" },
  { from: "c2", conn: "导致", to: "c1" },
  { from: "c1", conn: "变成", to: "c2" },
]);

test("剪掉指向已删概念或已删连接词的连线", () => {
  assert.deepEqual(pruneEdges(edges(), ["c1"], ["包括", "导致"]), []);
  assert.deepEqual(pruneEdges(edges(), ids(kit().concepts), ["包括"]),
    [{ from: "c1", conn: "包括", to: "c2" }]);
  assert.deepEqual(pruneEdges(edges(), ids(kit().concepts), ["包括", "导致"]), [
    { from: "c1", conn: "包括", to: "c2" },
    { from: "c2", conn: "导致", to: "c1" },
  ]);
});

test("剪掉已删概念的落点", () => {
  const placed = { c1: { x: 1, y: 2 }, c2: { x: 3, y: 4 } };
  assert.deepEqual(Object.keys(prunePlaced(placed, ["c2"])), ["c2"]);
  assert.deepEqual(Object.keys(prunePlaced(placed, ["c1", "c2"])), ["c1", "c2"]);
});
