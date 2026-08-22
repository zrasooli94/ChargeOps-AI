"use client";

import { useEffect, useRef } from "react";

export default function RobotWorkspace() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const move = (event: PointerEvent) => {
      const rect = node.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      node.style.setProperty("--mx", `${x * 18}px`);
      node.style.setProperty("--my", `${y * 12}px`);
    };
    node.addEventListener("pointermove", move);
    return () => node.removeEventListener("pointermove", move);
  }, []);

  return (
    <div className="robot-stage" ref={ref} aria-hidden="true">
      <div className="orb orb-a" />
      <div className="orb orb-b" />
      <div className="holo-panel holo-main">
        <div className="holo-topline"><span>ENERGY DEMAND</span><b>LIVE</b></div>
        <svg viewBox="0 0 420 160" className="hero-chart">
          <defs>
            <linearGradient id="area" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#7c3aed" stopOpacity=".38" />
              <stop offset="100%" stopColor="#7c3aed" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d="M10 132 C45 120, 61 116, 90 119 S137 88, 170 94 S216 79, 242 83 S290 47, 318 61 S360 29, 410 34 L410 160 L10 160Z" fill="url(#area)" />
          <path className="draw-line" d="M10 132 C45 120, 61 116, 90 119 S137 88, 170 94 S216 79, 242 83 S290 47, 318 61 S360 29, 410 34" fill="none" stroke="#6d28d9" strokeWidth="4" strokeLinecap="round" />
        </svg>
      </div>
      <div className="holo-panel holo-small small-one"><span>STATIONS</span><strong>1,248</strong><em>98.7% online</em></div>
      <div className="holo-panel holo-small small-two"><span>AGENT</span><strong>READY</strong><em>RAG grounded</em></div>
      <div className="robot-base"><span /></div>
      <div className="robot-arm robot-arm-one" />
      <div className="robot-joint joint-one" />
      <div className="robot-arm robot-arm-two" />
      <div className="robot-joint joint-two" />
      <div className="robot-gripper"><i /><i /></div>
      <div className="scan-ring ring-one" />
      <div className="scan-ring ring-two" />
      <div className="charger-pillar"><div className="charger-screen">ϟ</div><div className="charger-slot" /></div>
      <div className="floor-grid" />
    </div>
  );
}
