"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { Navigation } from "@/components/Navigation";
import { ledger } from "@/lib/api";

interface LedgerAccount {
  id: string;
  owner_type: string;
  owner_id?: string;
  account_kind?: string | null;
  created_at?: string;
}

interface LedgerEvent {
  id: string;
  ts: string;
  type: string;
  amount: { amount: string; currency: string };
  src_account_id?: string | null;
  dst_account_id?: string | null;
}

export default function LedgerPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [accounts, setAccounts] = useState<LedgerAccount[]>([]);
  const [events, setEvents] = useState<LedgerEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [highlightEventId] = useState(() => {
    if (typeof window === "undefined") return "";
    return new URLSearchParams(window.location.search).get("event") || "";
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

  useEffect(() => {
    if (!highlightEventId || loading) return;
    const el = document.getElementById(`ledger-event-${highlightEventId}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [highlightEventId, loading, events]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [accountsData, eventsData] = await Promise.all([
        ledger.getAccounts(50),
        ledger.getEvents(undefined, 50),
      ]);
      setAccounts(accountsData.items || accountsData || []);
      setEvents(eventsData.items || eventsData || []);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load ledger");
    } finally {
      setLoading(false);
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
          <h1
            style={{
              fontSize: "2rem",
              fontWeight: 700,
              marginBottom: "32px",
              color: "var(--text)",
            }}
          >
            Ledger Overview
          </h1>

          {error && (
            <div
              style={{
                padding: "12px",
                borderRadius: "8px",
                background: "rgba(239, 68, 68, 0.1)",
                color: "#ef4444",
                fontSize: "0.9rem",
                marginBottom: "24px",
              }}
            >
              {error}
            </div>
          )}

          {loading ? (
            <div
              style={{
                textAlign: "center",
                padding: "48px",
                color: "var(--text-muted)",
              }}
            >
              Loading ledger state...
            </div>
          ) : (
            <div className="responsive-grid responsive-grid-2">
              <div className="card">
                <h2
                  style={{
                    fontSize: "1.25rem",
                    fontWeight: 600,
                    marginBottom: "12px",
                    color: "var(--text)",
                  }}
                >
                  Accounts
                </h2>
                {accounts.length === 0 ? (
                  <p
                    style={{
                      fontSize: "0.9rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    No accounts yet.
                  </p>
                ) : (
                  <div
                    style={{
                      maxHeight: "320px",
                      overflowY: "auto",
                      fontSize: "0.85rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    {accounts.map((acc) => (
                      <div
                        key={acc.id}
                        style={{
                          padding: "8px 0",
                          borderBottom: "1px solid var(--border)",
                        }}
                      >
                        <div>
                          <strong>{acc.account_kind || "participant"}</strong>
                        </div>
                        <div>Owner type: {acc.owner_type}</div>
                        {acc.owner_id && <div>Owner id: {acc.owner_id}</div>}
                        <div
                          style={{
                            fontSize: "0.8rem",
                            color: "var(--text-muted)",
                          }}
                        >
                          id: {acc.id}
                        </div>
                      </div>
                    ))}
                  </div>
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
                  Recent Events
                </h2>
                {events.length === 0 ? (
                  <p
                    style={{
                      fontSize: "0.9rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    No ledger events yet.
                  </p>
                ) : (
                  <div
                    style={{
                      maxHeight: "320px",
                      overflowY: "auto",
                      fontSize: "0.85rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    {events.map((ev) => (
                      <div
                        id={`ledger-event-${ev.id}`}
                        key={ev.id}
                        style={{
                          padding: "8px 0",
                          borderBottom: "1px solid var(--border)",
                          background:
                            highlightEventId && highlightEventId === ev.id
                              ? "rgba(16, 185, 129, 0.12)"
                              : undefined,
                          borderRadius: highlightEventId === ev.id ? "8px" : undefined,
                          paddingLeft: highlightEventId === ev.id ? "8px" : undefined,
                        }}
                      >
                        <div>
                          <strong>{ev.type}</strong> — {ev.amount?.amount}{" "}
                          {ev.amount?.currency}
                        </div>
                        <div>
                          {ev.src_account_id && (
                            <>
                              From:{" "}
                              <span style={{ color: "var(--accent)" }}>
                                {ev.src_account_id}
                              </span>
                              {"  "}
                            </>
                          )}
                          {ev.dst_account_id && (
                            <>
                              To:{" "}
                              <span style={{ color: "var(--accent)" }}>
                                {ev.dst_account_id}
                              </span>
                            </>
                          )}
                        </div>
                        <div>
                          Time:{" "}
                          {new Date(ev.ts).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

