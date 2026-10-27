"""Inventory & Order Processing benchmark target module for automated program repair."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Item:
    item_id: str
    name: str
    unit_price: float
    stock_quantity: int
    min_stock_threshold: int = 5


@dataclass
class OrderItem:
    item_id: str
    quantity: int


@dataclass
class Order:
    order_id: str
    items: List[OrderItem]
    discount_rate: float = 0.0
    is_vip: bool = False


class InventoryManager:
    """Manages inventory stock levels, restock alerts, and order fulfillment."""

    def __init__(self):
        self.catalog: Dict[str, Item] = {}

    def add_item(self, item: Item) -> None:
        if item.item_id in self.catalog:
            raise ValueError(f"Item '{item.item_id}' already exists in catalog")
        if item.unit_price < 0:
            raise ValueError("Unit price cannot be negative")
        if item.stock_quantity < 0:
            raise ValueError("Stock quantity cannot be negative")
        self.catalog[item.item_id] = item

    def get_stock(self, item_id: str) -> int:
        if item_id not in self.catalog:
            raise KeyError(f"Item '{item_id}' not found in catalog")
        return self.catalog[item_id].stock_quantity

    def restock(self, item_id: str, quantity: int) -> int:
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive")
        if item_id not in self.catalog:
            raise KeyError(f"Item '{item_id}' not found in catalog")
        self.catalog[item_id].stock_quantity += quantity
        return self.catalog[item_id].stock_quantity

    def is_low_stock(self, item_id: str) -> bool:
        if item_id not in self.catalog:
            raise KeyError(f"Item '{item_id}' not found")
        item = self.catalog[item_id]
        return item.stock_quantity <= item.min_stock_threshold

    def calculate_order_total(self, order: Order) -> float:
        """Calculate total price of order with discount and VIP privileges."""
        if not order.items:
            return 0.0

        subtotal = 0.0
        for entry in order.items:
            if entry.quantity <= 0:
                raise ValueError("Order item quantity must be positive")
            if entry.item_id not in self.catalog:
                raise KeyError(f"Item '{entry.item_id}' not found")

            item = self.catalog[entry.item_id]
            subtotal += item.unit_price * entry.quantity

        discount = order.discount_rate
        if order.is_vip:
            discount += 0.05

        if discount > 0.50:
            discount = 0.50

        final_total = subtotal * (1.0 - discount)
        return round(final_total, 2)

    def fulfill_order(self, order: Order) -> bool:
        """
        Fulfill order if all items have sufficient stock.
        Deducts stock on success; aborts atomically on failure.
        """
        if not order.items:
            return False

        # First pass: verify sufficient stock for all requested items
        for entry in order.items:
            if entry.item_id not in self.catalog:
                raise KeyError(f"Item '{entry.item_id}' not found")
            item = self.catalog[entry.item_id]
            if item.stock_quantity < entry.quantity:
                return False

        # Second pass: deduct quantities
        for entry in order.items:
            self.catalog[entry.item_id].stock_quantity -= entry.quantity

        return True
