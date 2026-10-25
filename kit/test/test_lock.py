import pytest

import lock


class FakeUsage:
    def __init__(self, used):
        self.used = used

    def is_used(self, map_version):
        return map_version in self.used


def test_未使用时可改():
    lock.assert_mutable("v1", FakeUsage(set()))


def test_使用后拒绝修改():
    with pytest.raises(lock.LockError):
        lock.assert_mutable("v1", FakeUsage({"v1"}))


def test_其他版本不受影响():
    lock.assert_mutable("v2", FakeUsage({"v1"}))


def test_空版本直接拒绝():
    with pytest.raises(lock.LockError):
        lock.assert_mutable("", FakeUsage(set()))


def test_锁状态可由界面读():
    assert lock.lock_state("v1", FakeUsage({"v1"})) == "locked"
    assert lock.lock_state("v2", FakeUsage({"v1"})) == "mutable"
