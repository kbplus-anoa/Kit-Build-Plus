import submission
import targetmap

MAX_PROPOSITIONS = 500


class ValidationError(ValueError):
    """学生提交不满足 kit 约束。"""


def check_against_kit(kit: targetmap.Kit,
                      props: tuple[submission.SubmittedProposition, ...]) -> None:
    """只用 kit 内零件：越界概念、越界连接词、自环、超量一律拒绝。"""
    concepts = {c.concept_id for c in kit.concepts}
    connections = set(kit.connections)
    if len(props) > MAX_PROPOSITIONS:
        raise ValidationError("命题数量超上限: " + str(len(props)))
    seen: set[tuple[str, str, str]] = set()
    for prop in props:
        _check_one(prop, concepts, connections, seen)


def _check_one(prop, concepts: set, connections: set, seen: set) -> None:
    if prop.head_id not in concepts:
        raise ValidationError("使用了 kit 外概念: " + prop.head_id)
    if prop.tail_id not in concepts:
        raise ValidationError("使用了 kit 外概念: " + prop.tail_id)
    if prop.connection not in connections:
        raise ValidationError("使用了 kit 外连接词: " + prop.connection)
    if prop.head_id == prop.tail_id:
        raise ValidationError("不允许自环: " + prop.head_id)
    key = (prop.head_id, prop.connection, prop.tail_id)
    if key in seen:
        raise ValidationError("重复命题: " + str(key))
    seen.add(key)


def check_mode(mode: str) -> None:
    if mode not in submission.MODES:
        raise ValidationError("未知模式: " + str(mode))


def check_keys(participant_id: int, material_id: int, session: int) -> None:
    for name, value in (("participant_id", participant_id),
                        ("material_id", material_id), ("session", session)):
        if not isinstance(value, int) or value < 1:
            raise ValidationError(name + " 须为正整数")
