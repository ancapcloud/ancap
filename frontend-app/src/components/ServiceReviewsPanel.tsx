"use client";

import { FormEvent, useCallback, useEffect, useId, useState } from "react";
import { ApiError, serviceReviews } from "@/lib/api";

type ReviewItem = {
  id: string;
  reviewer_type: string;
  rating?: number | null;
  text?: string | null;
  created_at: string;
};

type Props = {
  targetType: "service" | "partner" | "literary_lot" | "listing" | "agent" | "strategy";
  targetId: string;
  label: string;
  reviewerUserId?: string;
};

export function ServiceReviewsPanel({ targetType, targetId, label, reviewerUserId }: Props) {
  const reviewFormId = useId();
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState(false);
  const [text, setText] = useState("");
  const [rating, setRating] = useState(5);

  const load = useCallback(async () => {
    try {
      const data = (await serviceReviews.list({
        target_type: targetType,
        target_id: targetId,
        limit: 40,
      })) as { items: ReviewItem[] };
      setItems(data.items || []);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load reviews");
    }
  }, [targetId, targetType]);

  useEffect(() => {
    void load();
  }, [load]);

  const onUserReview = async (e: FormEvent) => {
    e.preventDefault();
    if (!reviewerUserId) {
      setError("Sign in to leave a user review");
      return;
    }
    setBusy(true);
    setError("");
    setInfo("");
    try {
      await serviceReviews.create({
        reviewer_type: "user",
        reviewer_id: reviewerUserId,
        target_type: targetType,
        target_id: targetId,
        rating,
        text: text.trim() || undefined,
      });
      setText("");
      setInfo("Review saved");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review failed");
    } finally {
      setBusy(false);
    }
  };

  const onAiReview = async () => {
    setBusy(true);
    setError("");
    setInfo("");
    try {
      await serviceReviews.createAi({
        target_type: targetType,
        target_id: targetId,
        rating: 4,
        focus: label.slice(0, 200),
      });
      setInfo("AI review attached");
      await load();
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError("AI reviews are available to platform operators only.");
      } else {
        setError(err instanceof Error ? err.message : "AI review failed");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <h2 className="text-lg font-semibold text-white">Reviews — {label}</h2>
      <p className="mt-1 text-sm text-slate-500">User and AI notes for this service / partner / lot.</p>

      <form onSubmit={onUserReview} className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
        <label htmlFor={reviewFormId + "-rating"} className="text-sm text-slate-400">
          Rating
          <select
            id={reviewFormId + "-rating"}
            className="mt-1 block border border-white/15 bg-black/40 px-3 py-2 text-white"
            value={rating}
            onChange={(e) => setRating(Number(e.target.value))}
          >
            {[5, 4, 3, 2, 1].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
        <label htmlFor={reviewFormId + "-comment"} className="flex-1 text-sm text-slate-400">
          Comment
          <input
            id={reviewFormId + "-comment"}
            className="mt-1 block w-full border border-white/15 bg-black/40 px-3 py-2 text-white"
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={2000}
            placeholder="Optional note"
          />
        </label>
        <button
          type="submit"
          disabled={busy}
          className="border border-emerald-400/40 px-4 py-2 text-sm text-emerald-100 hover:bg-emerald-400/10 disabled:opacity-50"
        >
          Post user review
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => void onAiReview()}
          className="border border-violet-400/40 px-4 py-2 text-sm text-violet-100 hover:bg-violet-400/10 disabled:opacity-50"
        >
          Request AI review
        </button>
      </form>

      {error ? <p role="alert" className="mt-3 text-sm text-rose-400">{error}</p> : null}
      {info ? <p role="status" className="mt-2 text-sm text-emerald-400">{info}</p> : null}

      <ul className="mt-6 space-y-4">
        {items.length === 0 ? (
          <li className="text-sm text-slate-500">No reviews yet.</li>
        ) : (
          items.map((r) => (
            <li key={r.id} className="border-t border-white/10 pt-3 text-sm">
              <span className="uppercase tracking-wide text-slate-400">{r.reviewer_type}</span>
              {r.rating != null ? <span className="ml-2 text-amber-200/90">{r.rating}/5</span> : null}
              <p className="mt-1 text-slate-300">{r.text || "—"}</p>
              <p className="mt-1 text-xs text-slate-600">{new Date(r.created_at).toLocaleString()}</p>
            </li>
          ))
        )}
      </ul>
    </section>
  );
}
