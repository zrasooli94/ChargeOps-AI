"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { ForecastResponse } from "@/lib/types";
import { useDashboard } from "@/components/dashboard/dashboard-context";

function Chart({ data }: { data: { predicted_energy_kwh: number }[] }) {
  const path = useMemo(() => {
    if (!data.length) return "";
    const max = Math.max(...data.map((p) => p.predicted_energy_kwh), 1);
    return data.map((p, i) => {
      const x = 12 + (i / Math.max(data.length - 1, 1)) * 676;
      const y = 250 - (p.predicted_energy_kwh / max) * 210;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
    }).join(" ");
  }, [data]);
  return <svg className="forecast-chart" viewBox="0 0 700 270"><defs><linearGradient id="forecastFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#7c3aed" stopOpacity=".28"/><stop offset="1" stopColor="#7c3aed" stopOpacity="0"/></linearGradient></defs><path d={`${path} L688 260 L12 260 Z`} fill="url(#forecastFill)"/><path d={path} fill="none" stroke="#6d28d9" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"/></svg>;
}

export default function ForecastPage() {
  const { station } = useDashboard();
  const [hours, setHours] = useState(24);
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!station) return;
    setLoading(true); setError("");
    api.forecast(station.station_id, hours).then(setData).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [station?.station_id, hours]);

  return <div className="page-stack">
    <section className="page-hero compact"><div><div className="eyebrow">⌁ DEMAND INTELLIGENCE</div><h1>See the next peak before it arrives.</h1><p>ML forecasting across charging history, weather, temporal patterns, spatial context and mobility signals.</p></div><div className="select-card"><span>Forecast horizon</span><select value={hours} onChange={(e) => setHours(Number(e.target.value))}><option value={12}>12 hours</option><option value={24}>24 hours</option><option value={48}>48 hours</option></select></div></section>
    {loading && <div className="loading-line"/>}{error && <div className="form-error">{error}</div>}
    {data && <>
      <section className="metric-grid four"><article><span>Peak demand</span><strong>{data.summary.peak_energy_kwh.toFixed(1)} kWh</strong></article><article><span>Total forecast</span><strong>{data.summary.total_predicted_energy_kwh.toFixed(1)} kWh</strong></article><article><span>Average / hour</span><strong>{data.summary.average_hourly_energy_kwh.toFixed(1)} kWh</strong></article><article><span>Peak risk</span><strong className={`risk-${data.peak_risk}`}>{data.peak_risk.toUpperCase()}</strong></article></section>
      <section className="panel"><div className="panel-head"><div><span>Predicted hourly demand</span><b>Peak: {data.summary.peak_timestamp}</b></div><div className="pulse-tag">LIVE MODEL</div></div><Chart data={data.points}/></section>
      {data.history_source === "demo_simulation" && <div className="notice warn">This forecasting demo uses simulated charging history and should not be interpreted as measured operational data.</div>}
      <section className="data-table-wrap"><table><thead><tr><th>Timestamp</th><th>Predicted kWh</th><th>Risk</th><th>Temp °C</th><th>Rain mm</th><th>Mobility</th></tr></thead><tbody>{data.points.map((p) => <tr key={p.timestamp}><td>{p.timestamp}</td><td>{p.predicted_energy_kwh.toFixed(1)}</td><td>{p.risk_level}</td><td>{p.temperature_c ?? "—"}</td><td>{p.precipitation_mm ?? "—"}</td><td>{p.mobility_index ?? "—"}</td></tr>)}</tbody></table></section>
    </>}
  </div>;
}
