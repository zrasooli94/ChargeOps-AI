"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api, logout } from "@/lib/api";
import type { Station, User } from "@/lib/types";
import { DashboardContext } from "./dashboard-context";

const nav = [
  ["Agent", "/dashboard/agent", "✦"],
  ["Demand Forecast", "/dashboard/forecast", "⌁"],
  ["Incidents", "/dashboard/incidents", "△"],
  ["Knowledge", "/dashboard/knowledge", "▤"],
  ["Observability", "/dashboard/observability", "◎"],
  ["Users", "/dashboard/users", "◫"],
  ["System", "/dashboard/system", "◇"],
] as const;

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [stations, setStations] = useState<Station[]>([]);
  const [stationId, setStationIdState] = useState("");
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  async function refreshStations() {
    const data = await api.stations();
    setStations(data);
    let saved: string | null = null;

    try {
      saved = window.localStorage.getItem("chargeops_station_id");
    } catch {}
    const next = data.find((s) => s.station_id === saved)?.station_id ?? data[0]?.station_id ?? "";
    setStationIdState((current) => current || next);
  }

  useEffect(() => {
    let active = true;
  
    async function bootstrap() {
      // Authentication check
      try {
        const me = await api.me();
      
        if (!active) return;
        setUser(me);
      } catch (error) {
        console.error("Authentication check failed:", error);
      
        if (active) {
          window.location.replace("/");
        }
      
        return;
      }
    
      // Station loading should NEVER log the user out
      try {
        const stationData = await api.stations();
      
        if (!active) return;
      
        setStations(stationData);
      
        let saved: string | null = null;
      
        try {
          saved = window.localStorage.getItem("chargeops_station_id");
        } catch (error) {
          console.warn("Could not read saved station:", error);
        }
      
        const next =
          stationData.find((s) => s.station_id === saved)?.station_id ??
          stationData[0]?.station_id ??
          "";
      
        setStationIdState(next);
      } catch (error) {
        console.error("Could not load stations:", error);
      }
    }
  
    bootstrap();
  
    return () => {
      active = false;
    };
  }, []);

  function setStationId(value: string) {
    setStationIdState(value);

    try {
      window.localStorage.setItem("chargeops_station_id", value);
    } catch (error) {
      console.warn("Could not save station:", error);
    }
  }

  const station = useMemo(() => stations.find((s) => s.station_id === stationId) ?? null, [stations, stationId]);
  const allowedNav = nav.filter(([name]) => name !== "Users" || user?.role === "admin");

  return (
    <DashboardContext.Provider value={{ user, stations, station, setStationId, refreshStations }}>
      <div className={`app-shell ${collapsed ? "sidebar-collapsed" : ""}`}>
        <aside className={`app-sidebar ${mobileOpen ? "mobile-open" : ""}`}>
          <div className="sidebar-brand"><span>ϟ</span><div><b>ChargeOps</b><strong>AI</strong></div></div>
          <button className="collapse-button" onClick={() => setCollapsed((v) => !v)} aria-label="Toggle sidebar">{collapsed ? "→" : "←"}</button>
          <nav>
            {allowedNav.map(([name, href, icon]) => (
              <Link key={href} className={pathname === href ? "active" : ""} href={href} onClick={() => setMobileOpen(false)}><i>{icon}</i><span>{name}</span></Link>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <div className="sidebar-user"><span>{user?.email?.[0]?.toUpperCase() ?? "?"}</span><div><b>{user?.email ?? "Loading…"}</b><small>{user?.role ?? ""}</small></div></div>
            <button onClick={logout}>Log out</button>
          </div>
        </aside>

        <section className="app-main">
          <header className="app-topbar">
            <button className="mobile-menu" onClick={() => setMobileOpen((v) => !v)}>☰</button>
            <div className="station-select-wrap"><span>Station</span><select value={stationId} onChange={(e) => setStationId(e.target.value)}>{stations.map((s) => <option key={s.station_id} value={s.station_id}>{s.station_id} — {s.name}</option>)}</select></div>
            <div className="live-pill"><i /> Backend live</div>
          </header>
          <div className="app-content">{children}</div>
        </section>
      </div>
    </DashboardContext.Provider>
  );
}
