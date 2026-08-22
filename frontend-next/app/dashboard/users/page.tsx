"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import { useDashboard } from "@/components/dashboard/dashboard-context";

export default function UsersPage() {
  const { user: me } = useDashboard();
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const isAdmin = me?.role === "admin";
  async function load() { if (!isAdmin) return; try { setUsers(await api.users()); } catch (e) { setError(e instanceof Error ? e.message : "Could not load users."); } }
  useEffect(() => { load(); }, [isAdmin]);
  async function create(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); setBusy(true); try { await api.createUser(String(form.get("email")), String(form.get("password")), String(form.get("role"))); event.currentTarget.reset(); await load(); } catch (e) { setError(e instanceof Error ? e.message : "Could not create user."); } finally { setBusy(false); } }
  if (!isAdmin) return <div className="locked-page"><span>◫</span><h1>User management is protected.</h1><p>Administrator access is required.</p></div>;
  return <div className="page-stack"><section className="page-hero compact"><div><div className="eyebrow">◫ IDENTITY & RBAC</div><h1>People, roles and access.</h1><p>Create ChargeOps accounts, assign roles and control active access.</p></div></section>{error && <div className="form-error">{error}</div>}<section className="metric-grid three"><article><span>Total users</span><strong>{users.length}</strong></article><article><span>Active</span><strong>{users.filter((u) => u.is_active).length}</strong></article><article><span>Admins</span><strong>{users.filter((u) => u.role === "admin").length}</strong></article></section><section className="split-grid"><div className="panel"><div className="panel-head"><div><span>Create user</span><b>RBAC protected</b></div></div><form className="upload-form" onSubmit={create}><label>Email<input name="email" type="email" required/></label><label>Temporary password<input name="password" type="password" minLength={15} required/></label><label>Role<select name="role" defaultValue="viewer"><option value="viewer">Viewer</option><option value="operator">Operator</option><option value="admin">Admin</option></select></label><button disabled={busy}>Create account →</button></form></div><div className="panel"><div className="panel-head"><div><span>User directory</span><b>{users.length} accounts</b></div></div><div className="user-list">{users.map((user) => <article key={user.id}><div className="avatar">{user.email[0]?.toUpperCase()}</div><div><b>{user.email}</b><small>{user.is_active ? "Active" : "Inactive"}</small></div><select value={user.role} disabled={user.id === me?.id} onChange={async (e) => { await api.changeUserRole(user.id, e.target.value); await load(); }}><option value="viewer">Viewer</option><option value="operator">Operator</option><option value="admin">Admin</option></select><button disabled={user.id === me?.id} onClick={async () => { await api.changeUserStatus(user.id, !user.is_active); await load(); }}>{user.is_active ? "Deactivate" : "Activate"}</button></article>)}</div></div></section></div>;
}
