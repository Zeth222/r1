from bot.strategy import compute_strategy


def test_compute_strategy_adjust():
    res = compute_strategy(lp_delta=10.0, perp_position=0.0, price=2000.0, margin=500.0, atr=5.0, funding_apr=0.01)
    assert res.action == "adjust"
    assert res.hedge_size == -10.0
