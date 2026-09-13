# workspace 的 conftest.py — 阻止 pytest 加载根目录的 conftest
import sys
from pathlib import Path

import pytest

# 把 workspace/ 加入 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s03_provenance_gate import cart as s03_cart
from s03_provenance_gate import seen_products as s03_seen
from s04_fencing import cart as s04_cart
from s04_fencing import seen_products as s04_seen


@pytest.fixture(autouse=True)
def clean_state():
    """每个测试函数执行前自动清空状态（s03 和 s04 各有独立的模块级变量）。"""
    s03_seen.clear()
    s03_cart.clear()
    s04_seen.clear()
    s04_cart.clear()
