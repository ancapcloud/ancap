const RECOVERY_URL_QUERY_KEYS = ["txid", "txId", "hash", "txHash", "transactionHash"];
const RECOVERY_URL_PATH_MARKERS = new Set(["tx", "txs", "transaction", "transactions"]);

export type SmartPayParsedRecoveryRef = {
  txid: string;
  network: string | null;
  explorerUrl: string | null;
};

export type SmartPayRecoveryInputParseResult = {
  refs: SmartPayParsedRecoveryRef[];
  txids: string[];
  duplicateTokens: string[];
  invalidTokens: string[];
};

function trimRecoveryToken(value: string): string {
  return value
    .trim()
    .replace(/^["'`<([{]+/, "")
    .replace(/["'`>)}\],;:.]+$/, "");
}

function parseRecoveryUrlCandidate(candidate: string): URL | null {
  try {
    return new URL(candidate);
  } catch {
    if (/^[a-z0-9.-]+\.[a-z]{2,}(?:[/:?#]|$)/i.test(candidate)) {
      try {
        return new URL(`https://${candidate}`);
      } catch {
        return null;
      }
    }
    return null;
  }
}

function looksLikeStructuredLocator(candidate: string): boolean {
  return /^(?:[a-z][a-z0-9+.-]*:\/\/|www\.)/i.test(candidate) || /^[a-z0-9.-]+\.[a-z]{2,}(?:[/:?#]|$)/i.test(candidate) || /[/?#]/.test(candidate);
}

function inferRecoveryNetworkFromUrl(url: URL): string | null {
  const hostname = url.hostname.toLowerCase();
  const pathname = url.pathname.toLowerCase();

  if ((hostname === "bscscan.com" || hostname.endsWith(".bscscan.com"))) {
    return "bsc";
  }

  if ((hostname === "basescan.org" || hostname.endsWith(".basescan.org"))) {
    return "base";
  }

  if (hostname === "etherscan.io" || hostname.endsWith(".etherscan.io")) {
    return "ethereum";
  }

  if (
    (hostname === "ancap.cloud" || hostname.endsWith(".ancap.cloud"))
    && (pathname.includes("/acp/tx") || pathname.includes("/acp/transactions"))
  ) {
    return "acp";
  }

  return null;
}

function extractRecoveryRefFromUrl(candidate: string): SmartPayParsedRecoveryRef | null {
  const url = parseRecoveryUrlCandidate(candidate);
  if (!url) {
    return null;
  }

  for (const key of RECOVERY_URL_QUERY_KEYS) {
    const value = url.searchParams.get(key);
    const trimmed = trimRecoveryToken(decodeURIComponent(value ?? ""));
    if (trimmed) {
      return {
        txid: trimmed,
        network: inferRecoveryNetworkFromUrl(url),
        explorerUrl: url.toString(),
      };
    }
  }

  const segments = url.pathname
    .split("/")
    .map((segment) => trimRecoveryToken(decodeURIComponent(segment)))
    .filter(Boolean);

  for (let index = 0; index < segments.length; index += 1) {
    if (!RECOVERY_URL_PATH_MARKERS.has(segments[index]!.toLowerCase())) {
      continue;
    }
    const txid = segments[index + 1];
    if (txid) {
      return {
        txid,
        network: inferRecoveryNetworkFromUrl(url),
        explorerUrl: url.toString(),
      };
    }
  }

  return null;
}

function scoreRecoveryRef(ref: SmartPayParsedRecoveryRef): number {
  return (ref.explorerUrl ? 2 : 0) + (ref.network ? 1 : 0);
}

export function normalizeSmartPayRecoveryRef(value: string): SmartPayParsedRecoveryRef | null {
  const trimmed = trimRecoveryToken(value);
  if (!trimmed) {
    return null;
  }

  const fromUrl = extractRecoveryRefFromUrl(trimmed);
  if (fromUrl) {
    return fromUrl;
  }

  if (looksLikeStructuredLocator(trimmed)) {
    return null;
  }

  return {
    txid: trimmed,
    network: null,
    explorerUrl: null,
  };
}

function formatSmartPayRecoveryNetworkLabel(network: string | null): string {
  return network ? network.toUpperCase() : "Unspecified network";
}

export function formatSmartPayRecoveryRefPreview(ref: SmartPayParsedRecoveryRef): string {
  return `${formatSmartPayRecoveryNetworkLabel(ref.network)} · ${ref.txid} · ${ref.explorerUrl ? "explorer link preserved" : "raw tx hash only"}`;
}

export function normalizeSmartPayRecoveryToken(value: string): string | null {
  return normalizeSmartPayRecoveryRef(value)?.txid ?? null;
}

export function parseSmartPayRecoveryInput(input: string): SmartPayRecoveryInputParseResult {
  const refs: SmartPayParsedRecoveryRef[] = [];
  const tokenIndexByTxid = new Map<string, number>();
  const tokens = input.split(/[\s,;]+/);
  const duplicateTokens: string[] = [];
  const invalidTokens: string[] = [];

  for (const token of tokens) {
    const trimmed = trimRecoveryToken(token);
    if (!trimmed) {
      continue;
    }

    const ref = normalizeSmartPayRecoveryRef(trimmed);
    if (!ref) {
      invalidTokens.push(trimmed);
      continue;
    }

    const key = ref.txid.toLowerCase();
    const existingIndex = tokenIndexByTxid.get(key);
    if (existingIndex !== undefined) {
      duplicateTokens.push(trimmed);
      if (scoreRecoveryRef(ref) > scoreRecoveryRef(refs[existingIndex]!)) {
        refs[existingIndex] = ref;
      }
      continue;
    }

    tokenIndexByTxid.set(key, refs.length);
    refs.push(ref);
  }

  return { refs, txids: refs.map((ref) => ref.txid), duplicateTokens, invalidTokens };
}

export function extractSmartPayRecoveryTxs(input: string): string[] {
  return parseSmartPayRecoveryInput(input).txids;
}

export function canSubmitSmartPayRecoveryInput(input: string): boolean {
  const trimmed = input.trim();
  if (!trimmed) {
    return true;
  }
  return parseSmartPayRecoveryInput(input).txids.length > 0;
}

export function getSmartPayRecoveryInputBlockReason(input: string): string | null {
  const trimmed = input.trim();
  if (!trimmed) {
    return null;
  }

  const parsed = parseSmartPayRecoveryInput(input);
  if (parsed.txids.length > 0) {
    return null;
  }

  if (parsed.invalidTokens.length > 0) {
    return "No valid tx hash or explorer link was parsed from this recovery input. Fix the pasted values or clear the field to run a status-only recovery pass.";
  }

  return null;
}
