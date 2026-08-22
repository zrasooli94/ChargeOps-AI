"use client";

import { createContext, useContext } from "react";
import type { Station, User } from "@/lib/types";

type DashboardContextValue = {
  user: User | null;
  stations: Station[];
  station: Station | null;
  setStationId: (stationId: string) => void;
  refreshStations: () => Promise<void>;
};

export const DashboardContext = createContext<DashboardContextValue | null>(null);

export function useDashboard() {
  const value = useContext(DashboardContext);
  if (!value) throw new Error("useDashboard must be used inside DashboardShell");
  return value;
}
