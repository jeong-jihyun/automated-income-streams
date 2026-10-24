"""예시 쇼핑 API 모듈. Calculate prices and manage orders."""


def add_tax(price: int, rate: float = 0.1) -> int:
    """Add tax to a price.

    Args:
        price: Price before tax.
        rate: Tax rate between 0 and 1.

    Returns:
        Price after tax.
    """
    return round(price * (1 + rate))


class Cart:
    """A shopping cart that holds items."""

    def add(self, name: str, qty: int = 1) -> None:
        """Add an item to the cart."""

    def _internal(self):
        """Not part of the public API."""


async def fetch_order(order_id: str) -> dict:
    """Fetch an order by its id."""
