"use client";

import { useEffect } from "react";

const RELOAD_GUARD_KEY = "ancap_chunk_reload_once";

function isChunkLoadError(reason: unknown): boolean {
  if (!reason) return false;
  const msg =
    typeof reason === "string"
      ? reason
      : typeof reason === "object" && "message" in reason
        ? String((reason as { message?: unknown }).message ?? "")
        : "";
  const name =
    typeof reason === "object" && "name" in reason
      ? String((reason as { name?: unknown }).name ?? "")
      : "";
  return (
    name === "ChunkLoadError" ||
    /ChunkLoadError|Loading chunk [\w-]+ failed|_next\/static\/chunks|Failed to fetch dynamically imported module/i.test(
      msg
    )
  );
}

async function clearAppCaches(): Promise<void> {
  try {
    if ("caches" in window) {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
    }
  } catch {
    /* ignore */
  }
  try {
    const reg = await navigator.serviceWorker?.getRegistration();
    reg?.active?.postMessage({ type: "CLEAR_CACHES" });
    // Force the new SW (icons-only) to take over if waiting.
    await reg?.update();
  } catch {
    /* ignore */
  }
}

function hardReload(): void {
  const url = new URL(window.location.href);
  url.searchParams.set("_reload", String(Date.now()));
  window.location.replace(url.toString());
}

export function ChunkErrorRecovery() {
  useEffect(() => {
    // Drop stale query noise after a recovery reload.
    const url = new URL(window.location.href);
    if (url.searchParams.has("_reload")) {
      url.searchParams.delete("_reload");
      window.history.replaceState({}, "", url.pathname + url.search + url.hash);
      sessionStorage.removeItem(RELOAD_GUARD_KEY);
    }

    const recover = async () => {
      if (sessionStorage.getItem(RELOAD_GUARD_KEY) === "1") return;
      sessionStorage.setItem(RELOAD_GUARD_KEY, "1");
      await clearAppCaches();
      hardReload();
    };

    const onRejection = (event: PromiseRejectionEvent) => {
      if (!isChunkLoadError(event.reason)) return;
      event.preventDefault();
      void recover();
    };

    const onError = (event: ErrorEvent) => {
      if (!isChunkLoadError(event.error || event.message)) return;
      event.preventDefault();
      void recover();
    };

    window.addEventListener("unhandledrejection", onRejection);
    window.addEventListener("error", onError);
    return () => {
      window.removeEventListener("unhandledrejection", onRejection);
      window.removeEventListener("error", onError);
    };
  }, []);

  return null;
}
