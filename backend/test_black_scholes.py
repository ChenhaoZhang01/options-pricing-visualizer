"""Tests for the Black-Scholes engine.

Reference values cross-checked against the standard textbook example
(Hull, Options Futures and Other Derivatives) and put-call parity.
"""

import math

from black_scholes import price_and_greeks, implied_volatility


def test_call_price_reference():
    # S=42, K=40, r=0.10, sigma=0.20, T=0.5 -> call ~ 4.759, put ~ 0.808 (Hull)
    call = price_and_greeks(42, 40, 0.5, 0.10, 0.20, option_type="call")
    put = price_and_greeks(42, 40, 0.5, 0.10, 0.20, option_type="put")
    assert abs(call.price - 4.759) < 0.01
    assert abs(put.price - 0.808) < 0.01


def test_put_call_parity():
    # C - P = S*e^{-qT} - K*e^{-rT}
    S, K, T, r, sigma, q = 100, 95, 1.0, 0.03, 0.25, 0.01
    c = price_and_greeks(S, K, T, r, sigma, q, "call").price
    p = price_and_greeks(S, K, T, r, sigma, q, "put").price
    lhs = c - p
    rhs = S * math.exp(-q * T) - K * math.exp(-r * T)
    assert abs(lhs - rhs) < 1e-6


def test_call_delta_bounds():
    g = price_and_greeks(100, 100, 1.0, 0.05, 0.2, option_type="call")
    assert 0.0 < g.delta < 1.0
    assert g.gamma > 0
    assert g.vega > 0


def test_implied_vol_roundtrip():
    true_sigma = 0.27
    price = price_and_greeks(100, 105, 0.75, 0.04, true_sigma, option_type="call").price
    recovered = implied_volatility(price, 100, 105, 0.75, 0.04, option_type="call")
    assert abs(recovered - true_sigma) < 1e-4


if __name__ == "__main__":
    test_call_price_reference()
    test_put_call_parity()
    test_call_delta_bounds()
    test_implied_vol_roundtrip()
    print("all tests passed")
