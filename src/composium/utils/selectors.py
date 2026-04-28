from __future__ import annotations


def xpath_contains_id(view_id: str, *, prefix: str = './/*', postfix: str = '') -> str:
    """Build cross-platform xpath matching both resource-id (Android) and name (iOS).

    Usage:
        parent = xpath_contains_id("checkout_payment_root")
        # → 'xpath::.//*[contains(@resource-id, "checkout_payment_root") or contains(@name, "checkout_payment_root")]'
    """
    return f'xpath::{prefix}[contains(@resource-id, "{view_id}") or contains(@name, "{view_id}")]{postfix}'
