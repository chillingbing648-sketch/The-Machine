"""Comprehensive test and regression suite for Inventory target."""

import pytest
try:
    from inventory import Item, OrderItem, Order, InventoryManager
except ModuleNotFoundError:
    from benchmarks.inventory.inventory import Item, OrderItem, Order, InventoryManager


@pytest.fixture
def populated_inventory() -> InventoryManager:
    manager = InventoryManager()
    manager.add_item(Item("A1", "Widget", 10.0, 20, min_stock_threshold=5))
    manager.add_item(Item("B2", "Gadget", 25.0, 4, min_stock_threshold=5))
    manager.add_item(Item("C3", "Cable", 5.0, 0, min_stock_threshold=2))
    return manager


def test_add_item_success():
    manager = InventoryManager()
    manager.add_item(Item("D4", "Mouse", 15.0, 10))
    assert manager.get_stock("D4") == 10


def test_add_duplicate_item_raises(populated_inventory: InventoryManager):
    with pytest.raises(ValueError, match="already exists"):
        populated_inventory.add_item(Item("A1", "Duplicate Widget", 10.0, 5))


def test_add_item_negative_price():
    manager = InventoryManager()
    with pytest.raises(ValueError, match="price cannot be negative"):
        manager.add_item(Item("E5", "Bad Price", -5.0, 10))


def test_add_item_negative_stock():
    manager = InventoryManager()
    with pytest.raises(ValueError, match="Stock quantity cannot be negative"):
        manager.add_item(Item("F6", "Bad Stock", 10.0, -1))


def test_get_stock_not_found(populated_inventory: InventoryManager):
    with pytest.raises(KeyError, match="not found"):
        populated_inventory.get_stock("NON_EXISTENT")


def test_restock_positive(populated_inventory: InventoryManager):
    new_stock = populated_inventory.restock("A1", 15)
    assert new_stock == 35
    assert populated_inventory.get_stock("A1") == 35


def test_restock_invalid_quantity(populated_inventory: InventoryManager):
    with pytest.raises(ValueError, match="must be positive"):
        populated_inventory.restock("A1", 0)
    with pytest.raises(ValueError, match="must be positive"):
        populated_inventory.restock("A1", -10)


def test_is_low_stock(populated_inventory: InventoryManager):
    # A1 has 20 > 5 -> False
    assert populated_inventory.is_low_stock("A1") is False
    # B2 has 4 <= 5 -> True
    assert populated_inventory.is_low_stock("B2") is True
    # C3 has 0 <= 2 -> True
    assert populated_inventory.is_low_stock("C3") is True


def test_calculate_order_total_standard(populated_inventory: InventoryManager):
    order = Order("ORD-1", [OrderItem("A1", 2), OrderItem("B2", 1)])
    # 2*10.0 + 1*25.0 = 45.0
    assert populated_inventory.calculate_order_total(order) == 45.0


def test_calculate_order_total_with_discount(populated_inventory: InventoryManager):
    order = Order("ORD-2", [OrderItem("A1", 2)], discount_rate=0.10)
    # 20.0 * 0.90 = 18.0
    assert populated_inventory.calculate_order_total(order) == 18.0


def test_calculate_order_total_vip(populated_inventory: InventoryManager):
    order = Order("ORD-3", [OrderItem("A1", 2)], discount_rate=0.10, is_vip=True)
    # 20.0 * (1 - 0.15) = 17.0
    assert populated_inventory.calculate_order_total(order) == 17.0


def test_calculate_order_total_max_discount_cap(populated_inventory: InventoryManager):
    order = Order("ORD-4", [OrderItem("A1", 10)], discount_rate=0.80, is_vip=True)
    # Capped at 50% discount: 100.0 * 0.50 = 50.0
    assert populated_inventory.calculate_order_total(order) == 50.0


def test_calculate_order_total_empty():
    manager = InventoryManager()
    order = Order("ORD-EMPTY", [])
    assert manager.calculate_order_total(order) == 0.0


def test_fulfill_order_success(populated_inventory: InventoryManager):
    order = Order("ORD-5", [OrderItem("A1", 5), OrderItem("B2", 2)])
    success = populated_inventory.fulfill_order(order)
    assert success is True
    assert populated_inventory.get_stock("A1") == 15
    assert populated_inventory.get_stock("B2") == 2


def test_fulfill_order_insufficient_stock(populated_inventory: InventoryManager):
    order = Order("ORD-6", [OrderItem("A1", 2), OrderItem("B2", 10)])  # B2 only has 4
    success = populated_inventory.fulfill_order(order)
    assert success is False
    # Verify atomicity: A1 stock should NOT have been deducted
    assert populated_inventory.get_stock("A1") == 20
    assert populated_inventory.get_stock("B2") == 4


def test_fulfill_order_empty(populated_inventory: InventoryManager):
    order = Order("ORD-7", [])
    assert populated_inventory.fulfill_order(order) is False
