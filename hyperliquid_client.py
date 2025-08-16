"""Hyperliquid HTTP client with EIP-712 signing support.

This module provides minimal helpers to interact with the Hyperliquid REST API
using a wallet address and private key for signing. Only the wallet address is
required for public queries; the private key is only needed when submitting
orders or cancellations.

Environment variables used:
- ``HL_WALLET_ADDRESS``: public address of the user wallet.
- ``HL_PRIVATE_KEY``: private key used for signing (never logged).
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional

import httpx
from eth_account import Account
from eth_account.messages import encode_structured_data

# Hyperliquid API endpoints
API_BASE_URL = "https://api.hyperliquid.xyz"
INFO_URL = f"{API_BASE_URL}/info"
EXCHANGE_URL = f"{API_BASE_URL}/exchange"

logger = logging.getLogger(__name__)


def _get_wallet() -> str:
    wallet = os.getenv("HL_WALLET_ADDRESS")
    if not wallet:
        raise RuntimeError("HL_WALLET_ADDRESS not set")
    return wallet


def _get_private_key() -> Optional[str]:
    return os.getenv("HL_PRIVATE_KEY")


def sign_eip712(data: Dict[str, Any], private_key: str) -> str:
    """Sign an EIP-712 typed message and return the hex signature."""
    signable = encode_structured_data(primitive=data)
    signed = Account.sign_message(signable, private_key=private_key)
    return signed.signature.hex()


def get_hl_open_positions(wallet: str) -> Dict[str, Any]:
    """Fetch open positions for ``wallet``.

    This request does not require authentication.
    """
    payload = {"type": "userOpenPositions", "user": wallet}
    resp = httpx.post(INFO_URL, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _order_typed_data(order: Dict[str, Any]) -> Dict[str, Any]:
    """Build EIP-712 typed data structure for order signing."""
    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
            ],
            "Order": [
                {"name": "symbol", "type": "string"},
                {"name": "side", "type": "string"},
                {"name": "size", "type": "uint256"},
                {"name": "price", "type": "uint256"},
                {"name": "reduceOnly", "type": "bool"},
                {"name": "wallet", "type": "address"},
            ],
        },
        "domain": {"name": "Hyperliquid", "version": "1", "chainId": 42161},
        "primaryType": "Order",
        "message": order,
    }


def _cancel_typed_data(cancel: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
            ],
            "Cancel": [
                {"name": "orderId", "type": "string"},
                {"name": "wallet", "type": "address"},
            ],
        },
        "domain": {"name": "Hyperliquid", "version": "1", "chainId": 42161},
        "primaryType": "Cancel",
        "message": cancel,
    }


def place_order(symbol: str, side: str, size: float, price: Optional[float], reduce_only: bool = False) -> Dict[str, Any]:
    """Submit a signed order to Hyperliquid.

    If ``HL_PRIVATE_KEY`` is not defined the function logs and returns a
    placeholder response without sending a request.
    """
    wallet = _get_wallet()
    private_key = _get_private_key()
    if not private_key:
        logger.info("HL_PRIVATE_KEY not set – running in SAFE mode, order not sent")
        return {"status": "safe_mode"}

    order = {
        "symbol": symbol,
        "side": side,
        "size": size,
        "price": price or 0,
        "reduceOnly": reduce_only,
        "wallet": wallet,
    }
    typed = _order_typed_data(order)
    signature = sign_eip712(typed, private_key)
    body = {"order": order, "signature": signature, "wallet": wallet}
    resp = httpx.post(EXCHANGE_URL, json=body, timeout=10)
    resp.raise_for_status()
    return resp.json()


def cancel_order(order_id: str) -> Dict[str, Any]:
    """Cancel an existing order via signed request."""
    wallet = _get_wallet()
    private_key = _get_private_key()
    if not private_key:
        logger.info("HL_PRIVATE_KEY not set – running in SAFE mode, cancel not sent")
        return {"status": "safe_mode"}

    cancel = {"orderId": order_id, "wallet": wallet}
    typed = _cancel_typed_data(cancel)
    signature = sign_eip712(typed, private_key)
    body = {"cancel": cancel, "signature": signature, "wallet": wallet}
    resp = httpx.post(EXCHANGE_URL, json=body, timeout=10)
    resp.raise_for_status()
    return resp.json()

