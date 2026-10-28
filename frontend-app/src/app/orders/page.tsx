"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { Navigation } from "@/components/Navigation";
import { orders, listings } from "@/lib/api";

export default function OrdersPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [items, setItems] = useState<any[]>([]);
  const [, setListingsMap] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const normalizeCurrency = (currency?: string) => {
    const c = (currency || "ACP").toUpperCase();
    if (c === "VUSD" || c === "USD") return "ACP";
    return c;
  };

  const formatAmount = (amount?: string) => {
    if (!amount) return "0";
    const n = Number(amount);
    if (Number.isNaN(n)) return amount;
    return n % 1 === 0 ? String(n) : n.toFixed(2);
  };

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
      const [ordersData, listingsData] = await Promise.all([
        orders.list(50),
        listings.list(100),
      ]);
      setItems(ordersData.items || ordersData || []);
      const lm: Record<string, any> = {};
      (listingsData.items || listingsData || []).forEach((l: any) => {
        lm[l.id] = l;
      });
      setListingsMap(lm);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load orders");
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
            Orders
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
              Loading orders...
            </div>
          ) : items.length === 0 ? (
            <div
              className="card"
              style={{ padding: "32px", textAlign: "center" }}
            >
              <p
                style={{
                  fontSize: "0.95rem",
                  color: "var(--text-muted)",
                }}
              >
                No orders yet. Place an order through the Marketplace.
              </p>
            </div>
          ) : (
            <div className="responsive-grid responsive-grid-3">
              {items.map((o) => {

                const price = o.amount;
                return (
                  <div key={o.id} className="card">
                    <div className="card-header">
                      <div style={{ flex: 1 }}>
                        <h3
                          style={{
                            fontWeight: 600,
                            fontSize: "1.05rem",
                            color: "var(--text)",
                            margin: 0,
                          }}
                        >
                          Order #{o.id.slice(0, 8)}
                        </h3>
                        <div
                          style={{
                            fontSize: "0.85rem",
                            color: "var(--text-muted)",
                            marginTop: "4px",
                          }}
                        >
                          Listing:{" "}
                          <span style={{ color: "var(--accent)" }}>
                            {o.listing_id}
                          </span>
                        </div>
                      </div>
                      <span
                        className={`badge ${
                          o.status === "paid"
                            ? "badge-active"
                            : o.status === "pending"
                            ? "badge-warning"
                            : "badge-error"
                        }`}
                      >
                        {o.status}
                      </span>
                    </div>
                    {price && (
                      <div
                        style={{
                          fontSize: "0.9rem",
                          color: "var(--text-muted)",
                          marginTop: "8px",
                        }}
                      >
                        Amount:{" "}
                        <span
                          style={{
                            color: "var(--accent)",
                            fontWeight: 600,
                          }}
                        >
                          {formatAmount(price.amount)} {normalizeCurrency(price.currency)}
                        </span>
                      </div>
                    )}
                    <div
                      style={{
                        fontSize: "0.85rem",
                        color: "var(--text-muted)",
                        marginTop: "8px",
                      }}
                    >
                      Buyer: {o.buyer_type} {o.buyer_id}
                    </div>
                    <div
                      style={{
                        fontSize: "0.8rem",
                        color: "var(--text-muted)",
                        marginTop: "8px",
                      }}
                    >
                      Created:{" "}
                      {new Date(o.created_at).toLocaleString()}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

