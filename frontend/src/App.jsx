import React, { useEffect, useMemo, useState } from "react";
import GreekChart from "./GreekChart.jsx";

const DEFAULTS = {
  S: 100,
  K: 100,
  T: 1.0,
  r: 0.05,
  sigma: 0.2,
  q: 0.0,
  option_type: "call",
};

const GREEKS = ["price", "delta", "gamma", "vega", "theta", "rho"];

function Field({ label, name, value, step, onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="number"
        step={step}
        value={value}
        onChange={(e) => onChange(name, parseFloat(e.target.value))}
      />
    </label>
  );
}

export default function App() {
  const [params, setParams] = useState(DEFAULTS);
  const [point, setPoint] = useState(null);
  const [curve, setCurve] = useState([]);
  const [greek, setGreek] = useState("delta");
  const [error, setError] = useState(null);

  const update = (name, value) =>
    setParams((p) => ({ ...p, [name]: name === "option_type" ? value : value }));

  const spotRange = useMemo(() => {
    const lo = Math.max(1, params.S * 0.4);
    const hi = params.S * 1.6;
    return { S_min: lo, S_max: hi, steps: 80 };
  }, [params.S]);

  useEffect(() => {
    const ctrl = new AbortController();
    async function load() {
      try {
        setError(null);
        const [priceRes, curveRes] = await Promise.all([
          fetch("/api/price", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(params),
            signal: ctrl.signal,
          }),
          fetch("/api/curve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...params, ...spotRange }),
            signal: ctrl.signal,
          }),
        ]);
        if (!priceRes.ok || !curveRes.ok) throw new Error("API error");
        setPoint(await priceRes.json());
        setCurve((await curveRes.json()).points);
      } catch (e) {
        if (e.name !== "AbortError") setError(e.message);
      }
    }
    load();
    return () => ctrl.abort();
  }, [params, spotRange]);

  return (
    <div className="app">
      <h1>Options Pricing Visualizer</h1>
      <p className="sub">Black-Scholes-Merton pricing with live Greek curves.</p>

      <div className="layout">
        <div className="panel">
          <h2>Inputs</h2>
          <Field label="Spot (S)" name="S" value={params.S} step={1} onChange={update} />
          <Field label="Strike (K)" name="K" value={params.K} step={1} onChange={update} />
          <Field label="Years to expiry (T)" name="T" value={params.T} step={0.05} onChange={update} />
          <Field label="Rate (r)" name="r" value={params.r} step={0.005} onChange={update} />
          <Field label="Volatility (σ)" name="sigma" value={params.sigma} step={0.01} onChange={update} />
          <Field label="Dividend yield (q)" name="q" value={params.q} step={0.005} onChange={update} />
          <label className="field">
            <span>Type</span>
            <select
              value={params.option_type}
              onChange={(e) => update("option_type", e.target.value)}
            >
              <option value="call">Call</option>
              <option value="put">Put</option>
            </select>
          </label>

          {error && <p className="error">Backend not reachable — start the FastAPI server.</p>}

          {point && (
            <div className="greeks">
              <h2>Greeks @ S={params.S}</h2>
              {GREEKS.map((g) => (
                <div className="greek-row" key={g}>
                  <span>{g}</span>
                  <strong>{point[g].toFixed(4)}</strong>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="panel chart-panel">
          <div className="greek-tabs">
            {GREEKS.map((g) => (
              <button
                key={g}
                className={g === greek ? "active" : ""}
                onClick={() => setGreek(g)}
              >
                {g}
              </button>
            ))}
          </div>
          <GreekChart data={curve} greek={greek} strike={params.K} spot={params.S} />
        </div>
      </div>
      <style>{styles}</style>
    </div>
  );
}

const styles = `
  :root { color-scheme: dark; }
  body { margin: 0; font-family: ui-sans-serif, system-ui, sans-serif;
         background: #0d1117; color: #e6edf3; }
  .app { max-width: 1100px; margin: 0 auto; padding: 24px; }
  h1 { margin: 0; font-size: 28px; }
  .sub { color: #8b949e; margin-top: 4px; }
  .layout { display: grid; grid-template-columns: 320px 1fr; gap: 20px; margin-top: 20px; }
  .panel { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 16px; }
  .field { display: flex; justify-content: space-between; align-items: center; margin: 8px 0; }
  .field input, .field select { width: 120px; background: #0d1117; color: #e6edf3;
    border: 1px solid #30363d; border-radius: 6px; padding: 6px; }
  .greeks { margin-top: 16px; border-top: 1px solid #30363d; padding-top: 12px; }
  .greek-row { display: flex; justify-content: space-between; padding: 4px 0; }
  .greek-tabs { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
  .greek-tabs button { background: #21262d; color: #8b949e; border: 1px solid #30363d;
    border-radius: 6px; padding: 6px 12px; cursor: pointer; text-transform: capitalize; }
  .greek-tabs button.active { background: #1f6feb; color: white; border-color: #1f6feb; }
  .error { color: #f85149; font-size: 13px; }
`;
