"use client";

import Link from "next/link";
import { FormEvent, useRef, useState } from "react";
import { Navigation } from "@/components/Navigation";
import { useAuth } from "@/components/AuthProvider";
import { ApiError, paymentScanner } from "@/lib/api";

type ParseSource = "paste" | "qr" | "ocr";

async function decodeQrFromImageFile(file: File): Promise<string | null> {
  const Detector = (typeof window !== "undefined" ? (window as any).BarcodeDetector : null) as
    | (new (options?: { formats?: string[] }) => { detect: (source: ImageBitmap) => Promise<Array<{ rawValue?: string }>> })
    | undefined;
  if (!Detector || typeof createImageBitmap !== "function") return null;
  try {
    const detector = new Detector({ formats: ["qr_code"] });
    const bitmap = await createImageBitmap(file);
    try {
      const codes = await detector.detect(bitmap);
      const value = codes.find((item) => typeof item.rawValue === "string" && item.rawValue.trim())?.rawValue;
      return value?.trim() || null;
    } finally {
      bitmap.close?.();
    }
  } catch {
    return null;
  }
}

export default function PaymentScannerPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const [raw, setRaw] = useState("");
  const [source, setSource] = useState<ParseSource>("paste");
  const [preview, setPreview] = useState<any>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [photoName, setPhotoName] = useState("");
  const [photoPreviewUrl, setPhotoPreviewUrl] = useState<string | null>(null);
  const textInputRef = useRef<HTMLInputElement | null>(null);
  const photoInputRef = useRef<HTMLInputElement | null>(null);

  function clearPhotoPreview() {
    setPhotoName("");
    setPhotoPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
  }

  async function onParse(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setConfirmed(false);
    try {
      setPreview(await paymentScanner.parse(raw, source));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Parse failed");
    } finally {
      setBusy(false);
    }
  }

  async function onTextFileSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy(true);
    setError("");
    setConfirmed(false);
    clearPhotoPreview();
    try {
      const text = await file.text().catch(() => "");
      if (!text.trim()) {
        setError("Selected file is empty or not plain text.");
        return;
      }
      setSource("ocr");
      setRaw(text.trim());
      setPreview(await paymentScanner.parse(text.trim(), "ocr"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Text import failed");
    } finally {
      setBusy(false);
    }
  }

  async function onPhotoSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy(true);
    setError("");
    setConfirmed(false);
    clearPhotoPreview();
    setPhotoName(file.name);
    setPhotoPreviewUrl(URL.createObjectURL(file));
    try {
      const qrPayload = await decodeQrFromImageFile(file);
      if (qrPayload) {
        setSource("paste");
        setRaw(qrPayload);
        setPreview(await paymentScanner.parse(qrPayload, "paste"));
        return;
      }
      const parsed = await paymentScanner.parseImage(file);
      setSource("ocr");
      const noteLines = Array.isArray(parsed?.parse_notes) ? parsed.parse_notes.join("\n") : "";
      setRaw(
        [
          parsed?.label ? `Invoice #${parsed.label}` : null,
          parsed?.address ? `Pay to: ${parsed.address}` : null,
          parsed?.amount ? `Total due: ${parsed.amount}${parsed.currency ? ` ${parsed.currency}` : ""}` : null,
          parsed?.detected_network ? `Network: ${parsed.detected_network}` : null,
          noteLines || null,
        ]
          .filter(Boolean)
          .join("\n") || "(extracted from photo)",
      );
      setPreview(parsed);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Photo import failed. Try a clearer image, paste OCR text, or use a QR photo.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (!isLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen bg-[var(--bg)]">
        <Navigation />
        <main className="mx-auto max-w-lg px-4 py-16 text-center">
          <Link href="/login?next=/payment-scanner" className="text-emerald-300">
            Log in to use Payment Scanner
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-2xl px-4 py-10">
        <h1 className="text-3xl font-semibold">AI Payment Scanner</h1>
        <p className="mt-2 text-sm text-white/65">
          Paste a payment URI, invoice/receipt OCR text, or QR payload — or upload a photo/image of the document.
          Review the preview and manually confirm before executing Smart Pay.
        </p>
        <div className="mt-4 flex flex-wrap gap-2 text-sm">
          {(["paste", "ocr"] as ParseSource[]).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setSource(mode)}
              className={`rounded-full px-4 py-2 ${
                source === mode ? "bg-emerald-400 text-slate-950" : "border border-white/15"
              }`}
            >
              {mode === "paste" ? "Paste / QR text" : "Receipt / OCR text"}
            </button>
          ))}
          <button
            type="button"
            onClick={() => textInputRef.current?.click()}
            className="rounded-full border border-white/15 px-4 py-2"
          >
            Import text file
          </button>
          <button
            type="button"
            onClick={() => photoInputRef.current?.click()}
            className="rounded-full border border-white/15 px-4 py-2"
          >
            Import photo / image
          </button>
          <input
            ref={textInputRef}
            type="file"
            accept=".txt,.csv,.md,text/plain"
            className="hidden"
            onChange={onTextFileSelected}
          />
          <input
            ref={photoInputRef}
            type="file"
            accept="image/*,.jpg,.jpeg,.png,.webp,.gif"
            capture="environment"
            className="hidden"
            onChange={onPhotoSelected}
          />
        </div>
        {photoPreviewUrl ? (
          <div className="mt-4 overflow-hidden rounded-xl border border-white/10 bg-white/[0.03]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={photoPreviewUrl} alt={photoName || "Uploaded payment document"} className="max-h-56 w-full object-contain" />
            <p className="border-t border-white/10 px-3 py-2 text-xs text-white/55">{photoName || "Uploaded image"}</p>
          </div>
        ) : null}
        <form onSubmit={onParse} className="mt-6 space-y-3">
          <textarea
            className="min-h-[140px] w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
            placeholder={
              source === "ocr"
                ? "Invoice #123\nPay to: acp1...\nTotal due: 10.00 USDT"
                : "acp:address?amount=10 or invoice text..."
            }
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
          />
          <button
            type="submit"
            disabled={busy}
            className="rounded-full bg-emerald-400 px-5 py-2.5 text-sm font-semibold text-slate-950 disabled:opacity-60"
          >
            {busy ? "Parsing…" : "Preview payment"}
          </button>
        </form>
        {error ? <p className="mt-4 text-amber-200">{error}</p> : null}
        {preview ? (
          <section className="mt-8 rounded-2xl border border-white/10 bg-white/[0.03] p-5 text-sm">
            <div>Network: {preview.detected_network || "unknown"}</div>
            <div className="mt-1">Address: {preview.address || "—"}</div>
            <div className="mt-1">
              Amount: {preview.amount || "—"} {preview.currency || ""}
            </div>
            {preview.label ? <div className="mt-1">Label: {preview.label}</div> : null}
            <div className="mt-1">Confidence: {(preview.confidence * 100).toFixed(0)}%</div>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-white/65">
              {(preview.parse_notes || []).map((note: string) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
            <label className="mt-5 flex items-center gap-2">
              <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
              I reviewed this preview and want to proceed manually
            </label>
            {confirmed && preview.address ? (
              <div className="mt-4 flex flex-wrap gap-3">
                <Link
                  href={`/explorer/address/${encodeURIComponent(preview.address)}`}
                  className="rounded-full border border-white/15 px-4 py-2 text-sm font-semibold"
                >
                  Open address
                </Link>
                <Link href="/wallet" className="rounded-full bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950">
                  Continue in wallet
                </Link>
              </div>
            ) : null}
          </section>
        ) : null}
      </main>
    </div>
  );
}
