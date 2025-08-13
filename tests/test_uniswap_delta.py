from bot.data import uniswap


def test_position_delta_near_zero():
    position = {
        "liquidity": 1000,
        "tickLower": {"tick": -100},
        "tickUpper": {"tick": 100},
        "pool": {
            "sqrtPrice": str(1 << 96),
            "token0": {"symbol": "WETH", "decimals": "18"},
            "token1": {"symbol": "USDC", "decimals": "6"},
        },
    }
    delta = uniswap.position_delta(position)
    assert abs(delta) < 1e-6
