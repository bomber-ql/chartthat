"""pytest 全局夹具：业务测试默认关闭速率限制，避免固定窗口干扰批量用例。

限流本身的行为在 test_security.py 中通过显式构造中间件验证。
必须在 app.config / app.main 被导入前设置环境变量（settings 在导入时读取）。
"""
from __future__ import annotations

import os

os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
