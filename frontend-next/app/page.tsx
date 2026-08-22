import LoginCard from "@/components/auth/login-card";
import RobotWorkspace from "@/components/hero/robot-workspace";

export default function Home() {
  const demoEmail = process.env.CHARGEOPS_DEMO_EMAIL ?? "";
  const demoPassword = process.env.CHARGEOPS_DEMO_PASSWORD ?? "";

  return (
    <main className="landing-shell">
      <header className="landing-nav">
        <a className="brand" href="#"><span className="brand-mark">ϟ</span><b>ChargeOps</b><strong>AI</strong></a>
        <div className="system-pill"><i /> All systems operational</div>
      </header>

      <section className="landing-hero">
        <div className="hero-copy">
          <div className="eyebrow">✦ INTELLIGENT EV OPERATIONS</div>
          <h1>AI operations,<br/><span>in motion.</span></h1>
          <p>One bright control plane for EV charging demand, incidents, RAG knowledge, autonomous agents, human approvals and production telemetry.</p>
          <div className="hero-actions"><a href="#demo" className="primary-link">Open demo →</a><a href="#capabilities" className="ghost-link">Explore capabilities</a></div>
          <div id="demo"><LoginCard demoEmail={demoEmail} demoPassword={demoPassword} /></div>
        </div>
        <RobotWorkspace />
      </section>

      <div className="motion-ticker" aria-hidden="true">
        <div>FORECASTING · RAG · AGENTIC OPERATIONS · INCIDENT INTELLIGENCE · HUMAN APPROVAL · OBSERVABILITY · PGVECTOR · LANGGRAPH · FORECASTING · RAG · AGENTIC OPERATIONS ·</div>
      </div>

      <section className="capability-grid" id="capabilities">
        {[
          ["01", "Demand intelligence", "Forecast station demand from temporal, weather, spatial and mobility signals."],
          ["02", "Agentic operations", "Diagnose faults, invoke trusted tools and pause protected actions for human approval."],
          ["03", "RAG knowledge", "Retrieve grounded EV-charging guidance from vector-indexed technical documents."],
          ["04", "Production telemetry", "Inspect persistent runs, tool calls, latency and approval decisions."],
        ].map(([n, title, text]) => <article key={n}><span>{n}</span><h2>{title}</h2><p>{text}</p></article>)}
      </section>
    </main>
  );
}
