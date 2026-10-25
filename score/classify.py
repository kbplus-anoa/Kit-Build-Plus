import lookup
import report
import targetmap

Key = tuple[str, str, str]


def classify(target: targetmap.TargetMap, props) -> tuple[report.ErrorChain, ...]:
    """四类错误链。判定顺序刻意固定：reversed → leaving → excessive → lacking。

    顺序有意义：同一条错写的命题，既可能被看成"多余"，也可能被看成"方向错"。
    先判最具体的（方向），再判次具体的（连接词用错），最后才判泛化的多余。
    """
    expected = lookup.target_keys(target)
    given = lookup.submitted_keys(props)
    out: list[report.ErrorChain] = []
    out.extend(_reversed(expected, given))
    out.extend(_leaving(target, expected, given))
    out.extend(_excessive(expected, given))
    out.extend(_lacking(expected, given))
    return tuple(out)


def _reversed(expected, given) -> list[report.ErrorChain]:
    """方向反转：B-c->A 存在，学生写了 A-c->B，且 A-c->B 本身不在目标图。"""
    out = []
    for (head, conn, tail) in given:
        if (head, conn, tail) in expected:
            continue
        if (tail, conn, head) in expected:
            out.append(_chain(report.REVERSED, head, conn, tail))
    return out


def _leaving(target, expected, given) -> list[report.ErrorChain]:
    """游离连接：两端概念在目标图中成对出现过，但连接词不是那一条。

    且该错写既不是方向反转，也不是目标图里本就有的正确命题。
    """
    out = []
    for (head, conn, tail) in given:
        if (head, conn, tail) in expected:
            continue
        if (tail, conn, head) in expected:
            continue
        if _pair_exists(expected, head, tail):
            out.append(_chain(report.LEAVING, head, conn, tail))
    return out


def _excessive(expected, given) -> list[report.ErrorChain]:
    """多余连接：目标图里完全找不到这条，也不属于上面两类。"""
    out = []
    for (head, conn, tail) in given:
        if (head, conn, tail) in expected:
            continue
        if (tail, conn, head) in expected:
            continue
        if _pair_exists(expected, head, tail):
            continue
        out.append(_chain(report.EXCESSIVE, head, conn, tail))
    return out


def _lacking(expected, given) -> list[report.ErrorChain]:
    """缺失连接：目标图里有、学生没写。"""
    return [_chain(report.LACKING, h, c, t)
            for (h, c, t) in expected if (h, c, t) not in given]


def _pair_exists(expected, head: str, tail: str) -> bool:
    for (h, _, t) in expected:
        if h == head and t == tail:
            return True
    return False


def _chain(kind: str, head: str, connection: str,
           tail: str) -> report.ErrorChain:
    return report.ErrorChain(kind=kind, head_id=head,
                             connection=connection, tail_id=tail)
