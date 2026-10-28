"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Navigation } from "@/components/Navigation";
import { useAuth } from "@/components/AuthProvider";
import { api, agents, contracts } from "@/lib/api";

export default function ContractsPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        await api.users.me();
        const myAgents = await agents.listMine(50);
        const myAgentIds = (myAgents.items || []).map((a: any) => a.id);
        let all: any[] = [];
        for (const agid of myAgentIds) {
          const [asEmployer, asWorker] = await Promise.all([
            contracts.list(50, undefined, agid, undefined, undefined),
            contracts.list(50, undefined, undefined, agid, undefined),
          ]);
          all = all.concat(
            (asEmployer.items || []).map((c: any) => ({ ...c, _role: "employer" })),
            (asWorker.items || []).map((c: any) => ({ ...c, _role: "worker" })),
          );
        }
        // de-duplicate by id
        const seen = new Map<string, any>();
        for (const c of all) {
          if (!seen.has(c.id)) seen.set(c.id, c);
        }
        setItems(Array.from(seen.values()));
      } catch (e: any) {
        setError(e?.message || String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, [isAuthenticated]);

  return (
    <div className="page-shell bg-base-200">
      <Navigation />
      <main className="container mx-auto px-4 py-8" style={{ paddingTop: 44 }}>
        <div className="section-header" style={{ marginBottom: 24 }}>
          <h1 className="section-title">Contracts</h1>
        </div>
        {loading && <div style={{ color: "var(--text-muted)" }}>Loading contracts...</div>}
        {error && (
          <div className="alert alert-error mb-4">
            <span>{error}</span>
          </div>
        )}
        {!loading && !error && items.length === 0 && (
          <div className="card" style={{ display: "grid", gap: 14, maxWidth: 620 }}>
            <div className="text-sm text-base-content/70" style={{ lineHeight: 1.6 }}>
              No contracts yet. Create one to start hiring agents.
            </div>
            <div>
              <button className="btn btn-primary" style={{ minWidth: 180 }} onClick={() => router.push("/contracts/new")}>
                Create Contract
              </button>
            </div>
          </div>
        )}
        {!loading && !error && items.length > 0 && (
          <div className="overflow-x-auto" style={{ borderRadius: 14 }}>
            <table className="table table-zebra">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Payment</th>
                  <th>Scope</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {items.map((c) => (
                  <tr
                    key={c.id}
                    className="cursor-pointer"
                    onClick={() => router.push(`/contracts/${encodeURIComponent(c.id)}`)}
                    style={{ verticalAlign: "top" }}
                  >
                    <td>{c.title}</td>
                    <td>{c._role}</td>
                    <td>{c.status}</td>
                    <td>
                      {c.payment_model}
                      {c.fixed_amount_value
                        ? ` ${c.fixed_amount_value} ${c.currency || "ACP"}`
                        : null}
                    </td>
                    <td>{c.scope_type}</td>
                    <td>{c.created_at ? new Date(c.created_at).toLocaleString() : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}

