"""开发者模式的门槛：写库前先要密码。

密码先固定，改在 DEV_PASSWORD 这一处；前端那道门只是顺手，真正的门在这里。
"""

DEV_PASSWORD = "1234321"


class GateError(RuntimeError):
    """密码不对，拒改。"""


def assert_open(password: str) -> None:
    """密码不对就抛 GateError；空串同样不放行。"""
    if password != DEV_PASSWORD:
        raise GateError("开发者密码不对")
