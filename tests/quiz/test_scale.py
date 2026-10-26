"""TAM 条目表：题数、构念分布、可选项、不收人口学题。"""

from kbp.contracts.tam import ATT, BI, PEOU, PU
from kbp.quiz import scale


def test_共十四题():
    assert len(scale.TAM_ITEMS) == 14


def test_题号唯一且前缀是构念代码():
    ids = [i.item_id for i in scale.TAM_ITEMS]
    assert len(set(ids)) == len(ids)
    assert all(i.item_id.startswith(i.construct) for i in scale.TAM_ITEMS)


def test_各构念题数():
    assert len(scale.items_of(PU)) == 4
    assert len(scale.items_of(PEOU)) == 4
    assert len(scale.items_of(BI)) == 3
    assert len(scale.items_of(ATT)) == 3


def test_态度三题标为可选其余必答():
    optional = [i.item_id for i in scale.TAM_ITEMS if i.optional]
    assert optional == ["ATT1", "ATT2", "ATT3"]
    assert [i.item_id for i in scale.TAM_ITEMS if not i.optional] == \
        ["PU1", "PU2", "PU3", "PU4", "PEOU1", "PEOU2", "PEOU3", "PEOU4",
         "BI1", "BI2", "BI3"]


def test_不收人口学题():
    text = " ".join(i.text for i in scale.TAM_ITEMS)
    assert "性别" not in text and "年龄段" not in text


def test_题干都是中文整句():
    for item in scale.TAM_ITEMS:
        assert item.text.endswith("。")
        assert len(item.text) >= 8


def test_items_of_未知构念为空():
    assert scale.items_of("XYZ") == ()


def test_item_ids_返回题号集合():
    ids = scale.item_ids()
    assert ids == frozenset(i.item_id for i in scale.TAM_ITEMS)
    assert "PU1" in ids and "性别" not in ids
