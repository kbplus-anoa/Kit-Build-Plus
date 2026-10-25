import adjudication


class LockError(RuntimeError):
    """目标图版本已锁定，拒绝修改。"""


def assert_mutable(map_version: str, usage: adjudication.MapUsagePort) -> None:
    """改目标图前的门槛：该版本一旦有学生用过即不可改。"""
    if not map_version:
        raise LockError("版本号不得为空")
    if usage.is_used(map_version):
        raise LockError("版本已被学生使用，不可修改: " + map_version)


def lock_state(map_version: str,
               usage: adjudication.MapUsagePort) -> str:
    """返回可读状态，供界面显示。"""
    return "locked" if usage.is_used(map_version) else "mutable"
