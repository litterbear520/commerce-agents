"""门控逻辑的单元测试。

从 s03_provenance_gate 导入被测函数，不调用任何外部 API。
后续步骤加的门控（注入防护、变体检查、数量上限）也往这里加。
"""
from s03_provenance_gate import (
    check_provenance,
    seen_products,
    cart,
    add_to_cart,
    update_cart_item,
    remember_products,
)


# ── check_provenance ───────────────────────────────────────────────

def test_unseen_id_is_held():
    """没见过的 ID 被 provenance 门控拦截。"""
    result = check_provenance("XYZ-999")
    assert result is not None
    assert result.blocked == "provenance"


def test_seen_id_passes():
    """见过的 ID 放行（返回 None）。"""
    seen_products["AR-1105"] = {"id": "AR-1105", "title": "ACME Select 主动降噪耳机"}
    result = check_provenance("AR-1105")
    assert result is None


def test_held_text_contains_recovery_hint():
    """拦截结果的文本里包含恢复提示，告诉模型怎么做。"""
    result = check_provenance("XYZ-999")
    assert result is not None
    assert "get_product_details" in result.text
    assert "search_products" in result.text


# ── add_to_cart 门控 ───────────────────────────────────────────────

def test_add_to_cart_requires_provenance():
    """add_to_cart 对没见过的 ID 返回 held，不是 error。"""
    result = add_to_cart("XYZ-999")
    assert result.blocked == "provenance"
    assert len(cart) == 0


def test_add_to_cart_allows_seen_id():
    """add_to_cart 对见过的、有库存的 ID 正常执行。"""
    remember_products([{"id": "AR-1104", "title": "ACME Select 矮轴机械键盘",
                        "price": 99.0, "rating": 4.6, "in_stock": True,
                        "description": "..."}])
    result = add_to_cart("AR-1104")
    assert result.blocked is None
    assert result.is_error is False
    assert len(cart) == 1
    assert cart[0]["product_id"] == "AR-1104"


def test_add_to_cart_rejects_out_of_stock():
    """add_to_cart 对见过但缺货的商品返回 error。"""
    remember_products([{"id": "AR-1002", "title": "ACME Signature 15Bar 意式咖啡机（带蒸汽棒）",
                        "price": 329.0, "rating": 4.7, "in_stock": False,
                        "description": "..."}])
    result = add_to_cart("AR-1002")
    assert result.is_error is True
    assert "缺货" in result.text
    assert len(cart) == 0


# ── update_cart_item 门控 ──────────────────────────────────────────

def test_update_cart_item_requires_provenance():
    """update_cart_item 对没见过的 ID 同样被拦截。"""
    result = update_cart_item("XYZ-999", 3)
    assert result.blocked == "provenance"
