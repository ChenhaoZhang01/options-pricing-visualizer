# Options Pricing Visualizer

Interactive **Black-Scholes-Merton** option calculator with live **Greeks**
visualization. A Python pricing engine serves prices and Greek curves; a
React + D3 frontend plots how each Greek behaves as the spot moves.

![stack](https://img.shields.io/badge/stack-React%20·%20D3%20·%20Python-1f6feb)

## Why it's interesting

It demonstrates the *math*, not just the plumbing:

- Full closed-form pricing for European calls and puts with continuous
  dividend yield `q`.
- All five primary Greeks (delta, gamma, vega, theta, rho) derived
  analytically, plus `d1`/`d2`.
- **Implied volatility** solver (Newton-Raphson with a bisection fallback).
- Correctness pinned by tests: a Hull textbook reference value and
  **put-call parity** to 1e-6.

## Architecture

```
backend/   FastAPI + pure-Python Black-Scholes (no numpy)
  black_scholes.py   pricing + Greeks + implied vol
  main.py            /price  /curve  /implied-vol  /health
  test_black_scholes.py
frontend/  React + D3 (Vite)
  src/App.jsx        input panel + live fetch
  src/GreekChart.jsx D3 line chart of Greek vs spot
```

## Run it

### Backend
```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxies /api -> :8000)
```

## API

| Endpoint        | Body                                              | Returns                |
|-----------------|---------------------------------------------------|------------------------|
| `POST /price`   | `S,K,T,r,sigma,q,option_type`                     | price + all Greeks     |
| `POST /curve`   | price body + `S_min,S_max,steps`                  | Greeks across spot     |
| `POST /implied-vol` | `target_price,S,K,T,r,q,option_type`          | implied volatility     |

## Tests
```bash
cd backend && python test_black_scholes.py
# or: pytest
```

## The math

For a call with spot `S`, strike `K`, time `T`, rate `r`, vol `σ`, yield `q`:

```
d1 = [ln(S/K) + (r - q + σ²/2)T] / (σ√T)
d2 = d1 - σ√T
C  = S·e^{-qT}·N(d1) - K·e^{-rT}·N(d2)
```

Greeks are the partial derivatives of `C` (or `P`) — see
[`black_scholes.py`](backend/black_scholes.py) for each one.
