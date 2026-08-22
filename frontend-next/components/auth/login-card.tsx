"use client";

import { FormEvent, useState } from "react";
import { login } from "@/lib/api";

export default function LoginCard({ demoEmail, demoPassword }: { demoEmail: string; demoPassword: string }) {
  const [email, setEmail] = useState(demoEmail);
  const [password, setPassword] = useState(demoPassword);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email.trim(), password);
      window.location.href = "/dashboard/agent";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
      setLoading(false);
    }
  }

  return (
    <form className="login-card" onSubmit={submit}>
      <div className="login-card-head">
        <div className="lock-dot">ϟ</div>
        <div><strong>Experience ChargeOps AI</strong><span>Demo access is prefilled and ready.</span></div>
      </div>
      <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" /></label>
      <label>Password<input value={password} onChange={(e) => setPassword(e.target.value)} type="password" autoComplete="current-password" /></label>
      {error && <div className="form-error">{error}</div>}
      <button className="primary-button" disabled={loading}>{loading ? "Connecting…" : "Enter ChargeOps →"}</button>
      <small>Read-only demo access is recommended for public portfolio visitors.</small>
    </form>
  );
}
