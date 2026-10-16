"use client";

import Link from "next/link";
import { useEffect, useId, useState, type FormEvent } from "react";
import { safeGetItem, safeRemoveItem, safeSetItem } from "@/lib/safeStorage";
import { reviewTrustByLang } from "@/locales/reviewTrust";
import { useLanguage } from "./LanguageProvider";
import s from "./WorkflowPresentation.module.css";

type TestFeedback = { version: 1; rating: number; text: string };
const PROJECT_ID_PATTERN = /^[a-z0-9][a-z0-9-]{0,79}$/;
const RATING_OPTIONS = [1, 2, 3, 4, 5];

function parseFeedback(raw: string): TestFeedback | null {
  try {
    const row: unknown = JSON.parse(raw);
    if (!row || typeof row !== "object") return null;
    const data = row as Record<string, unknown>;
    if (data.version !== 1 || typeof data.rating !== "number" || !Number.isInteger(data.rating) ||
      data.rating < 1 || data.rating > 5 || typeof data.text !== "string" ||
      !data.text.trim() || data.text.length > 2000) return null;
    return { version: 1, rating: data.rating, text: data.text };
  } catch {
    return null;
  }
}

/** Personal test feedback only: no API, account identity, publication or aggregate rating. */
export function TestProjectFeedback({ projectId }: { projectId: string }) {
  const { lang } = useLanguage();
  const c = reviewTrustByLang[lang];
  const formId = useId();
  const validProject = PROJECT_ID_PATTERN.test(projectId);
  const storageKey = `ancap:test-project-feedback:v1:${projectId}`;
  const [loaded, setLoaded] = useState(false);
  const [saved, setSaved] = useState<TestFeedback | null>(null);
  const [editing, setEditing] = useState(false);
  const [rating, setRating] = useState<number | null>(null);
  const [text, setText] = useState("");
  const [error, setError] = useState<"storageError" | "deleteError" | "readError" | "validationError" | null>(null);
  const [notice, setNotice] = useState<"saved" | "deleted" | null>(null);

  useEffect(() => {
    const raw = validProject ? safeGetItem(storageKey) : null;
    const feedback = raw ? parseFeedback(raw) : null;
    setSaved(feedback);
    setRating(feedback?.rating ?? null);
    setText(feedback?.text ?? "");
    setEditing(false);
    setError(raw && !feedback ? "readError" : null);
    setNotice(null);
    setLoaded(true);
  }, [storageKey, validProject]);

  const onSave = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setNotice(null);
    if (!validProject || rating === null || !RATING_OPTIONS.includes(rating) || !text.trim() || text.length > 2000) {
      setError("validationError");
      return;
    }
    const feedback: TestFeedback = { version: 1, rating, text: text.trim() };
    const serialized = JSON.stringify(feedback);
    safeSetItem(storageKey, serialized);
    if (safeGetItem(storageKey) !== serialized) {
      setError("storageError");
      return;
    }
    setSaved(feedback);
    setText(feedback.text);
    setEditing(false);
    setError(null);
    setNotice("saved");
  };

  const onDelete = () => {
    setNotice(null);
    safeRemoveItem(storageKey);
    if (safeGetItem(storageKey) !== null) {
      setError("deleteError");
      return;
    }
    setSaved(null);
    setRating(null);
    setText("");
    setEditing(false);
    setError(null);
    setNotice("deleted");
  };

  return <div className={s.deliverable} data-testid={`test-feedback-${projectId}`} style={{ marginTop: 20, overflowWrap: "anywhere" }} aria-labelledby={`${formId}-title`}>
    <h4 id={`${formId}-title`} style={{ fontSize: 16, margin: "0 0 10px", fontWeight: 650 }}>{c.feedbackTitle}</h4>
    <span className={s.tag}>{c.localBadge}</span>
    <p id={`${formId}-note`} style={{ marginTop: 12 }}>{c.localNote}</p>
    {!validProject ? <p role="alert">{c.invalidProject}</p> : loaded ? <>
      {saved && !editing ? <div>
        <strong>{c.savedTitle}</strong>
        <p aria-label={c.ratingChoice.replace("{rating}", String(saved.rating))}>{saved.rating} / 5</p>
        <p style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{saved.text}</p>
        <div className={s.actions} style={{ marginTop: 12 }}>
          <button type="button" className={s.secondary} onClick={() => {
            setRating(saved.rating); setText(saved.text); setEditing(true); setNotice(null); setError(null);
          }}>{c.edit}</button>
          <button type="button" className={s.secondary} onClick={onDelete}>{c.remove}</button>
        </div>
      </div> : <form onSubmit={onSave} aria-describedby={`${formId}-note`}>
        <fieldset style={{ border: 0, padding: 0, margin: "16px 0" }}>
          <legend style={{ fontSize: 14, marginBottom: 10 }}>{c.rating}</legend>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
            {RATING_OPTIONS.map((value) => <label key={value} style={{ display: "inline-flex", alignItems: "center", gap: 8, minHeight: 44, padding: "4px 10px", border: "1px solid var(--border)", borderRadius: 8 }}>
              <input type="radio" name={`${formId}-rating`} value={value} checked={rating === value} required
                onChange={() => setRating(value)} aria-label={c.ratingChoice.replace("{rating}", String(value))} />
              <span aria-hidden="true">{value}</span>
            </label>)}
          </div>
        </fieldset>
        <label htmlFor={`${formId}-text`} style={{ display: "block", fontSize: 14, marginBottom: 8 }}>{c.comment}</label>
        <textarea id={`${formId}-text`} value={text} onChange={(event) => setText(event.target.value)}
          rows={3} required maxLength={2000} placeholder={c.placeholder} aria-describedby={`${formId}-limit`}
          style={{ display: "block", width: "100%", maxWidth: "100%", boxSizing: "border-box", resize: "vertical", border: "1px solid var(--border)", borderRadius: 8, background: "var(--bg)", color: "var(--text)", padding: 12, font: "inherit", fontSize: 14 }} />
        <p id={`${formId}-limit`} style={{ fontSize: 12 }}>{c.textLimit}</p>
        <div className={s.actions} style={{ marginTop: 12 }}>
          <button type="submit" className={s.secondary}>{c.save}</button>
          {saved ? <button type="button" className={s.secondary} onClick={() => {
            setRating(saved.rating); setText(saved.text); setEditing(false); setError(null); setNotice(null);
          }}>{c.cancel}</button> : null}
        </div>
      </form>}
      {error ? <p role="alert" style={{ marginTop: 12 }}>{c[error]}</p> : null}
      {notice ? <p role="status" style={{ marginTop: 12 }}>{c[notice]}</p> : null}
    </> : null}
  </div>;
}

export function ReviewTrustSection({ compact = false }: { compact?: boolean }) {
  const { lang } = useLanguage();
  const c = reviewTrustByLang[lang];
  const headingId = useId();

  return <section id="project-reviews" className={s.section} aria-labelledby={headingId}>
    <p className={s.eyebrow}>{c.eyebrow}</p>
    <h2 id={headingId} className={s.heading}>{c.title}</h2>
    <span className={s.tag}>{c.badge}</span>
    <p className={s.lead} style={{ marginTop: 16 }}>{c.lead}</p>
    {!compact ? <div className={s.grid}>
      <div className={s.card}>
        <h3>{c.criteriaTitle}</h3>
        <ul style={{ paddingLeft: 20, color: "var(--text-muted)", lineHeight: 1.8, fontSize: 14 }}>
          {c.criteria.map((criterion) => <li key={criterion}>{criterion}</li>)}
        </ul>
      </div>
      <div className={s.card}><h3>{c.separationTitle}</h3><p>{c.separationBody}</p></div>
      <div className={s.card}><h3>{c.verificationTitle}</h3><p>{c.verificationBody}</p></div>
    </div> : null}
    <p className={s.note}>{c.note}</p>
    <div className={s.actions}><Link className={s.secondary} href="/ai/workflows">{c.catalog}</Link></div>
  </section>;
}
