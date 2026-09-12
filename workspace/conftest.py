# workspace 的 conftest.py — 阻止 pytest 加载根目录的 conftest
import sys
from pathlib import Path

import pytest

# 把 workspace/ 加入 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s03_provenance_gate import seen_products, cart


@pytest.fixture(autouse=True)
def clean_state():
    """每个测试函数执行前自动清空状态。"""
    seen_products.clear()
    cart.clear()
