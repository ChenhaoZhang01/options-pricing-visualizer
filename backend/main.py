"""FastAPI server exposing Black-Scholes pricing and Greek surfaces."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from black_scholes import price_and_greeks, implied_volatility

app = FastAPI(title="Options Pricing Visualizer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PriceRequest(BaseModel):
    S: float = Field(..., gt=0, description="Spot price")
    K: float = Field(..., gt=0, description="Strike price")
    T: float = Field(..., gt=0, description="Years to expiry")
    r: float = Field(..., description="Risk-free rate (e.g. 0.05)")
    sigma: float = Field(..., gt=0, description="Volatility (e.g. 0.2)")
    q: float = Field(0.0, description="Dividend yield")
    option_type: str = Field("call", pattern="^(call|put)$")


class IVRequest(BaseModel):
    target_price: float = Field(..., gt=0)
    S: float = Field(..., gt=0)
    K: float = Field(..., gt=0)
    T: float = Field(..., gt=0)
    r: float
    q: float = 0.0
    option_type: str = Field("call", pattern="^(call|put)$")


class CurveRequest(PriceRequest):
    # Vary the spot from S_min..S_max and report Greeks along the curve.
    S_min: float = Field(..., gt=0)
    S_max: float = Field(..., gt=0)
    steps: int = Field(60, ge=2, le=500)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/price")
def price(req: PriceRequest):
    try:
        g = price_and_greeks(req.S, req.K, req.T, req.r, req.sigma, req.q, req.option_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return g.as_dict()


@app.post("/implied-vol")
def iv(req: IVRequest):
    sigma = implied_volatility(
        req.target_price, req.S, req.K, req.T, req.r, req.q, req.option_type
    )
    return {"implied_volatility": sigma}


@app.post("/curve")
def curve(req: CurveRequest):
    """Return Greeks across a range of spot prices for D3 surface plots."""
    if req.S_max <= req.S_min:
        raise HTTPException(status_code=400, detail="S_max must exceed S_min")
    points = []
    dx = (req.S_max - req.S_min) / (req.steps - 1)
    for i in range(req.steps):
        s = req.S_min + i * dx
        g = price_and_greeks(s, req.K, req.T, req.r, req.sigma, req.q, req.option_type)
        points.append({"S": s, **g.as_dict()})
    return {"points": points}
