"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { Navigation } from "@/components/Navigation";
import { runs, strategies, pools, system as systemApi } from "@/lib/api";

interface Run {
  id: string;
  strategy_version_id: string;
  pool_id: string;
  state: string;
  created_at: string;
  started_at?: string;
  finished_at?: string;
}

export default function RunsPage() {
  const [runFeePercent, setRunFeePercent] = useState<number>(1);
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [runsList, setRunsList] = useState<Run[]>([]);
  const [strategiesList, setStrategiesList] = useState<any[]>([]);
  const [poolsList, setPoolsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState({
    strategy_id: "",
    pool_id: "",
    dry_run: true,
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [runsData, strategiesData, poolsData, feeCfg] = await Promise.all([
        runs.list(50),
        strategies.list(50),
        pools.list(50),
        systemApi.fees().catch(() => null),
      ]);
      setRunsList(runsData.items || []);
      setStrategiesList(strategiesData.items || []);
      setPoolsList(poolsData.items || []);
      const pct = Number((feeCfg as any)?.run_fee_percent ?? "0");
      if (Number.isFinite(pct) && pct >= 0) setRunFeePercent(pct);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError("");

    try {
      const strategy = strategiesList.find(s => s.id === formData.strategy_id);
      if (!strategy) {
        throw new Error("Strategy not found");
      }

      const versionsData = await strategies.getVersions(formData.strategy_id, 1);
      const latestVersion = versionsData.items?.[0];

      if (!latestVersion) {
        throw new Error("Strategy has no versions");
      }

      await runs.create({
        strategy_version_id: latestVersion.id,
        pool_id: formData.pool_id,
        dry_run: formData.dry_run,
        params: {},
      });

      setShowCreateModal(false);
      setFormData({ strategy_id: "", pool_id: "", dry_run: true });
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to create run");
    } finally {
      setCreating(false);
    }
  };

  if (authLoading || !isAuthenticated) {
    return null;
  }



  return (
    <>

      <div className="min-h-screen">
        <Navigation />

        <div className="container" style={{ padding: "48px 24px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "32px" }}>
            <h1 style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text)" }}>
              Runs
            </h1>
            <button 
              className="btn btn-primary"
              onClick={() => setShowCreateModal(true)}
              disabled={strategiesList.length === 0 || poolsList.length === 0}
            >
              Create Run
            </button>
          </div>

          {error && (
            <div style={{
              padding: "12px",
              borderRadius: "8px",
              background: "rgba(239, 68, 68, 0.1)",
              color: "#ef4444",
              fontSize: "0.9rem",
              marginBottom: "24px",
            }}>
              {error}
            </div>
          )}

          {(strategiesList.length === 0 || poolsList.length === 0) && !loading && (
            <div className="card" style={{ marginBottom: "24px", padding: "16px", background: "rgba(255, 193, 7, 0.1)" }}>
              <p style={{ color: "#ffc107", margin: 0, fontSize: "0.9rem" }}>
                You need to create a strategy and a pool before running strategies.
              </p>
            </div>
          )}

          {loading ? (
            <div style={{ textAlign: "center", padding: "48px", color: "var(--text-muted)" }}>
              Loading runs...
            </div>
          ) : runsList.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: "48px" }}>
              <p style={{ color: "var(--text-muted)", marginBottom: "16px" }}>
                No runs yet. Create your first run to execute a strategy.
              </p>
              {strategiesList.length > 0 && poolsList.length > 0 && (
                <button 
                  className="btn btn-primary"
                  onClick={() => setShowCreateModal(true)}
                >
                  Create Run
                </button>
              )}
            </div>
          ) : (
            <div className="responsive-grid responsive-grid-3">
              {runsList.map((run) => (
                <a key={run.id} className="card" href={`/runs/${encodeURIComponent(run.id)}`} style={{ textDecoration: "none" }}>
                  <div className="card-header">
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text)", marginBottom: "8px" }}>
                        Run #{run.id.slice(0, 8)}
                      </div>
                      <div style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>
                        Created: {new Date(run.created_at).toLocaleString()}
                      </div>
                    </div>
                    <span className={`badge ${
                      run.state === "completed" ? "badge-success" :
                      run.state === "running" ? "badge-info" :
                      run.state === "failed" ? "badge-error" :
                      "badge-warning"
                    }`}>
                      {run.state}
                    </span>
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
      </div>

      {showCreateModal && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(0, 0, 0, 0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
          padding: "24px",
        }}>
          <div className="card" style={{ maxWidth: "500px", width: "100%" }}>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 600, marginBottom: "24px", color: "var(--text)" }}>
              Create New Run
            </h2>
            <form onSubmit={handleCreate}>
              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", marginBottom: "8px", fontSize: "0.9rem", fontWeight: 500, color: "var(--text)" }}>
                  Strategy *
                </label>
                <select
                  value={formData.strategy_id}
                  onChange={(e) => setFormData({ ...formData, strategy_id: e.target.value })}
                  required
                  style={{
                    width: "100%",
                    padding: "12px",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                    background: "var(--bg)",
                    color: "var(--text)",
                    fontSize: "0.95rem",
                  }}
                >
                  <option value="">Select a strategy</option>
                  {strategiesList.map((strategy) => (
                    <option key={strategy.id} value={strategy.id}>
                      {strategy.name}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", marginBottom: "8px", fontSize: "0.9rem", fontWeight: 500, color: "var(--text)" }}>
                  Pool *
                </label>
                <select
                  value={formData.pool_id}
                  onChange={(e) => setFormData({ ...formData, pool_id: e.target.value })}
                  required
                  style={{
                    width: "100%",
                    padding: "12px",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                    background: "var(--bg)",
                    color: "var(--text)",
                    fontSize: "0.95rem",
                  }}
                >
                  <option value="">Select a pool</option>
                  {poolsList.map((pool) => (
                    <option key={pool.id} value={pool.id}>
                      {pool.name}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: "24px" }}>
                <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={formData.dry_run}
                    onChange={(e) => setFormData({ ...formData, dry_run: e.target.checked })}
                    style={{ width: "18px", height: "18px" }}
                  />
                  <span style={{ fontSize: "0.9rem", color: "var(--text)" }}>
                    Dry run (test mode, no real execution)
                  </span>
                </label>
              </div>
              <div style={{ marginBottom: "16px", color: "var(--text-muted)", fontSize: "0.85rem" }}>
                Platform run fee: {runFeePercent}% is charged only from contract payout (if any).
              </div>

              <div style={{ display: "flex", gap: "12px" }}>
                <button
                  type="submit"
                  disabled={creating}
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                >
                  {creating ? "Creating..." : "Create Run"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn btn-ghost"
                  style={{ flex: 1 }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
