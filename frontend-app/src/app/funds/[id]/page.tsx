"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { Navigation } from "@/components/Navigation";
import { funds, strategies } from "@/lib/api";

export default function FundDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const fundId = Array.isArray(params?.id) ? params.id[0] : (params?.id as string | undefined);

  const [fund, setFund] = useState<any | null>(null);
  const [performance, setPerformance] = useState<any | null>(null);
  const [, setStrategiesList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [allocating, setAllocating] = useState(false);
  const [allocForm, setAllocForm] = useState({
    strategy_version_id: "",
    weight: 0.1,
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  const loadData = useCallback(async () => {
    if (!fundId) return;
    try {
      setLoading(true);
      const [fundData, perfData, strategiesData] = await Promise.all([
        funds.get(fundId),
        funds.getPerformance(fundId),
        strategies.list(100),
      ]);
      setFund(fundData);
      setPerformance(perfData);
      setStrategiesList(strategiesData.items || []);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load fund");
    } finally {
      setLoading(false);
    }
  }, [fundId]);

  useEffect(() => {
    if (isAuthenticated && fundId) {
      loadData();
    }
  }, [isAuthenticated, fundId, loadData]);

  const handleAllocate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fundId) return;
    setAllocating(true);
    setError("");

    try {
      await funds.allocate(fundId, {
        strategy_version_id: allocForm.strategy_version_id,
        weight: allocForm.weight,
      });
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to allocate fund");
    } finally {
      setAllocating(false);
    }
  };

  if (!fundId || authLoading || !isAuthenticated) {
    return null;
  }

  return (
    <>

      <div className="min-h-screen">
        <Navigation />

        <div className="container" style={{ padding: "48px 24px" }}>
          <button
            onClick={() => router.push("/funds")}
            style={{
              marginBottom: "16px",
              fontSize: "0.9rem",
              color: "var(--text-muted)",
              textDecoration: "none",
            }}
          >
            ← Back to funds
          </button>

          {loading ? (
            <div
              style={{
                textAlign: "center",
                padding: "48px",
                color: "var(--text-muted)",
              }}
            >
              Loading fund...
            </div>
          ) : error ? (
            <div
              style={{
                padding: "12px",
                borderRadius: "8px",
                background: "rgba(239, 68, 68, 0.1)",
                color: "#ef4444",
                fontSize: "0.9rem",
              }}
            >
              {error}
            </div>
          ) : fund ? (
            <>
              <h1
                style={{
                  fontSize: "2rem",
                  fontWeight: 700,
                  marginBottom: "24px",
                  color: "var(--text)",
                }}
              >
                Fund: {fund.name}
              </h1>

              <div
                className="responsive-grid responsive-grid-2"
                style={{ marginBottom: "32px" }}
              >
                <div className="card">
                  <h2
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 600,
                      marginBottom: "12px",
                      color: "var(--text)",
                    }}
                  >
                    Allocations
                  </h2>
                  {performance?.allocations?.length ? (
                    <ul
                      style={{
                        listStyle: "none",
                        padding: 0,
                        margin: 0,
                        fontSize: "0.9rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      {performance.allocations.map((alloc: any) => {
                        const evalItem =
                          performance.evaluation_summary?.find(
                            (p: any) =>
                              p.strategy_version_id ===
                              alloc.strategy_version_id,
                          );
                        return (
                          <li
                            key={alloc.id}
                            style={{
                              padding: "8px 0",
                              borderBottom: "1px solid var(--border)",
                            }}
                          >
                            <div>
                              Strategy version:{" "}
                              <span style={{ color: "var(--accent)" }}>
                                {alloc.strategy_version_id}
                              </span>
                            </div>
                            <div>Weight: {(alloc.weight * 100).toFixed(1)}%</div>
                            {evalItem && (
                              <div>
                                Score:{" "}
                                {evalItem.score != null
                                  ? evalItem.score.toFixed(3)
                                  : "n/a"}{" "}
                                ({evalItem.sample_size ?? 0} samples)
                              </div>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    <p
                      style={{
                        fontSize: "0.9rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      No allocations yet. Use the form on the right to add one.
                    </p>
                  )}
                </div>

                <div className="card">
                  <h2
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 600,
                      marginBottom: "12px",
                      color: "var(--text)",
                    }}
                  >
                    Add Allocation
                  </h2>
                  <form onSubmit={handleAllocate}>
                    <div style={{ marginBottom: "16px" }}>
                      <label
                        style={{
                          display: "block",
                          marginBottom: "8px",
                          fontSize: "0.9rem",
                          fontWeight: 500,
                          color: "var(--text)",
                        }}
                      >
                        Strategy Version *
                      </label>
                      <input
                        type="text"
                        value={allocForm.strategy_version_id}
                        onChange={(e) =>
                          setAllocForm({
                            ...allocForm,
                            strategy_version_id: e.target.value,
                          })
                        }
                        placeholder="strategy_version_id"
                        required
                        style={{
                          width: "100%",
                          padding: "12px",
                          borderRadius: "8px",
                          border: "1px solid var(--border)",
                          background: "var(--bg)",
                          color: "var(--text)",
                          fontSize: "0.95rem",
                          marginBottom: "4px",
                        }}
                      />
                      <div
                        style={{
                          fontSize: "0.8rem",
                          color: "var(--text-muted)",
                        }}
                      >
                        Use a concrete strategy version id. (UI integration with
                        strategies will be added later.)
                      </div>
                    </div>

                    <div style={{ marginBottom: "16px" }}>
                      <label
                        style={{
                          display: "block",
                          marginBottom: "8px",
                          fontSize: "0.9rem",
                          fontWeight: 500,
                          color: "var(--text)",
                        }}
                      >
                        Weight (0–1)
                      </label>
                      <input
                        type="number"
                        min={0}
                        max={1}
                        step={0.01}
                        value={allocForm.weight}
                        onChange={(e) =>
                          setAllocForm({
                            ...allocForm,
                            weight: parseFloat(e.target.value || "0"),
                          })
                        }
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
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={allocating}
                      className="btn btn-primary"
                      style={{ width: "100%" }}
                    >
                      {allocating ? "Allocating..." : "Add Allocation"}
                    </button>
                  </form>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </>
  );
}

