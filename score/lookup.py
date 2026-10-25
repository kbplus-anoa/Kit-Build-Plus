import targetmap

Key = tuple[str, str, str]


def key(head_id: str, connection: str, tail_id: str) -> Key:
    """命题的查表键：起端、连接词、末端。kit 封闭 ⇒ 查表即可判定。"""
    return (head_id, connection, tail_id)


def target_keys(target: targetmap.TargetMap) -> dict[Key, None]:
    """目标命题集合，保持原顺序，供判定与差值计算。"""
    order: dict[Key, None] = {}
    for prop in target.propositions:
        order.setdefault(key(prop.head_id, prop.connection, prop.tail_id), None)
    return order


def submitted_keys(props) -> dict[Key, None]:
    order: dict[Key, None] = {}
    for prop in props:
        order.setdefault(key(prop.head_id, prop.connection, prop.tail_id), None)
    return order


def count_correct(target: targetmap.TargetMap,
                  props) -> int:
    """正确命题数：学生提交的每条命题是否在目标图中。"""
    expected = target_keys(target)
    return sum(1 for k in submitted_keys(props) if k in expected)


def unmatched(target: targetmap.TargetMap,
              props) -> tuple[Key, ...]:
    """学生写了但目标图里没有的命题，按提交顺序。"""
    expected = target_keys(target)
    return tuple(k for k in submitted_keys(props) if k not in expected)


def missing(target: targetmap.TargetMap,
            props) -> tuple[Key, ...]:
    """目标图里有但学生没写的命题，按目标图顺序。"""
    given = submitted_keys(props)
    return tuple(k for k in target_keys(target) if k not in given)
