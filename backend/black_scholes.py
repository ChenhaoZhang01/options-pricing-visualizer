"""Black-Scholes option pricing and Greeks.

Pure-Python implementation (no numpy required) of the Black-Scholes-Merton
model for European options with continuous dividend yield.

All Greeks are returned per the standard market conventions:
  - delta:  dV/dS
  - gamma:  d2V/dS2
  - vega:   dV/dsigma   (per 1.00 change in vol; divide by 100 for "per 1%")
  - theta:  dV/dt       (per year; divide by 365 for "per day")
  - rho:    dV/dr       (per 1.00 change in rate; divide by 100 for "per 1%")
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Literal

OptionType = Literal["call", "put"]

SQRT_2PI = math.sqrt(2.0 * math.pi)


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def _norm_cdf(x: float) -> float:
    # 0.5 * erfc(-x / sqrt(2)); math.erf is accurate and stdlib.
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


@dataclass
class Greeks:
    price: float
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    d1: float
    d2: float

    def as_dict(self) -> dict:
        return asdict(self)


def _d1_d2(S: float, K: float, T: float, r: float, sigma: float, q: float):
    if T <= 0 or sigma <= 0:
        raise ValueError("T and sigma must be positive")
    vol_sqrt_t = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    return d1, d2


def price_and_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: OptionType = "call",
) -> Greeks:
    """Compute Black-Scholes price and the five primary Greeks.

    S: spot, K: strike, T: years to expiry, r: risk-free rate,
    sigma: volatility, q: dividend yield, option_type: 'call' or 'put'.
    """
    if S <= 0 or K <= 0:
        raise ValueError("S and K must be positive")
    if option_type not in ("call", "put"):
        raise ValueError("option_type must be 'call' or 'put'")

    d1, d2 = _d1_d2(S, K, T, r, sigma, q)
    Nd1, Nd2 = _norm_cdf(d1), _norm_cdf(d2)
    nd1 = _norm_pdf(d1)
    disc_r = math.exp(-r * T)
    disc_q = math.exp(-q * T)
    sqrt_t = math.sqrt(T)

    if option_type == "call":
        price = S * disc_q * Nd1 - K * disc_r * Nd2
        delta = disc_q * Nd1
        theta = (
            -(S * disc_q * nd1 * sigma) / (2 * sqrt_t)
            - r * K * disc_r * Nd2
            + q * S * disc_q * Nd1
        )
        rho = K * T * disc_r * Nd2
    else:
        price = K * disc_r * _norm_cdf(-d2) - S * disc_q * _norm_cdf(-d1)
        delta = -disc_q * _norm_cdf(-d1)
        theta = (
            -(S * disc_q * nd1 * sigma) / (2 * sqrt_t)
            + r * K * disc_r * _norm_cdf(-d2)
            - q * S * disc_q * _norm_cdf(-d1)
        )
        rho = -K * T * disc_r * _norm_cdf(-d2)

    gamma = (disc_q * nd1) / (S * sigma * sqrt_t)
    vega = S * disc_q * nd1 * sqrt_t

    return Greeks(
        price=price,
        delta=delta,
        gamma=gamma,
        vega=vega,
        theta=theta,
        rho=rho,
        d1=d1,
        d2=d2,
    )


def implied_volatility(
    target_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float = 0.0,
    option_type: OptionType = "call",
    tol: float = 1e-8,
    max_iter: int = 100,
) -> float:
    """Recover implied vol from a market price via Newton-Raphson with a
    bisection fallback for robustness."""
    lo, hi = 1e-6, 5.0
    sigma = 0.2  # initial guess

    for _ in range(max_iter):
        g = price_and_greeks(S, K, T, r, sigma, q, option_type)
        diff = g.price - target_price
        if abs(diff) < tol:
            return sigma
        if g.vega > 1e-10:
            step = diff / g.vega
            sigma_next = sigma - step
            if lo < sigma_next < hi:
                sigma = sigma_next
                continue
        # Bisection fallback
        mid = price_and_greeks(S, K, T, r, sigma, q, option_type).price
        if mid > target_price:
            hi = sigma
        else:
            lo = sigma
        sigma = 0.5 * (lo + hi)

    return sigma
