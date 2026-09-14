"""购物 agent 的共享库。导出外部调用方需要的类型和后端抽象类。

执行器、门控、提示词从各自的子模块导入。
"""

from .backend import NotOffered, StorefrontBackend, Unavailable
from .types import (
    Cart,
    CartItem,
    Product,
    ProductDetails,
    SearchFilters,
    ShoppingSessionContext,
    ShoppingSessionState,
)

__all__ = [
    "Cart",
    "CartItem",
    "NotOffered",
    "Product",
    "ProductDetails",
    "SearchFilters",
    "ShoppingSessionContext",
    "ShoppingSessionState",
    "StorefrontBackend",
    "Unavailable",
]
