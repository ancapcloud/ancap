import * as SecureStore from "expo-secure-store";
import type {
  SmartPayExecution,
  SmartPayHistoryEntry as SmartPayApiHistoryEntry,
  SmartPayPaymentIntent,
  SmartPayQuote,
  SmartPayReceipt,
} from "@ancap/acp-api-client";

const KEY_SMART_PAY_HISTORY = "acp_wallet_smart_pay_history";
const MAX_HISTORY_ITEMS = 8;

const STORE_OPTIONS: SecureStore.SecureStoreOptions = {
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
};

export type SmartPayHistorySnapshotOrigin = "local" | "backend" | "local+backend";

export type SmartPayHistoryEntry = {
  id: string;
  savedAt: string;
  intent: SmartPayPaymentIntent;
  quote: SmartPayQuote | null;
  execution: SmartPayExecution;
  receipt?: SmartPayReceipt | null;
  sessionToken?: string | null;
  snapshotOrigin?: SmartPayHistorySnapshotOrigin;
};

export type PersistedSmartPayHistory = {
  version: 1;
  entries: SmartPayHistoryEntry[];
};

export type SmartPayHistoryRemoteOptions = {
  hasAccountAuth?: boolean;
  limit?: number;
  listRemoteHistory?: (limit: number) => Promise<SmartPayApiHistoryEntry[]>;
};

export type SmartPayHistoryClearOptions = SmartPayHistoryRemoteOptions;
export type SmartPayHistoryLoadOptions = SmartPayHistoryRemoteOptions;

function parseTimestamp(value: string | null | undefined): number {
  if (!value) return 0;
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function executionStatusRank(status: SmartPayExecution["status"]): number {
  switch (status) {
    case "awaiting_local_signature":
      return 0;
    case "pending_reconciliation":
      return 1;
    case "failed":
      return 2;
    case "completed":
      return 3;
    default:
      return -1;
  }
}

function executionScore(execution: SmartPayExecution): number {
  return (
    executionStatusRank(execution.status) * 100 +
    execution.txRefs.length * 10 +
    (execution.progress?.observedTxCount ?? 0) * 5 +
    (execution.progress ? 1 : 0) +
    (execution.nextAction ? 1 : 0) +
    (execution.error ? 1 : 0)
  );
}

function receiptScore(receipt: SmartPayReceipt | null | undefined): number {
  if (!receipt) return -1;
  return receipt.txRefs.length * 10 + receipt.routeSummary.length * 3 + receipt.networkFees.length * 2 + (receipt.merchantLabel ? 1 : 0);
}

function entryTimestamp(entry: SmartPayHistoryEntry): number {
  return Math.max(
    parseTimestamp(entry.execution.updatedAt),
    parseTimestamp(entry.execution.createdAt),
    parseTimestamp(entry.receipt?.completedAt),
    parseTimestamp(entry.savedAt),
    parseTimestamp(entry.intent.createdAt)
  );
}

function compareExecution(a: SmartPayExecution, b: SmartPayExecution): number {
  const timestampDiff =
    Math.max(parseTimestamp(a.updatedAt), parseTimestamp(a.createdAt)) -
    Math.max(parseTimestamp(b.updatedAt), parseTimestamp(b.createdAt));
  if (timestampDiff !== 0) return timestampDiff;
  return executionScore(a) - executionScore(b);
}

function compareReceipt(a: SmartPayReceipt | null | undefined, b: SmartPayReceipt | null | undefined): number {
  const timestampDiff = parseTimestamp(a?.completedAt) - parseTimestamp(b?.completedAt);
  if (timestampDiff !== 0) return timestampDiff;
  return receiptScore(a) - receiptScore(b);
}

function getExecutionTxRefKey(ref: SmartPayExecution["txRefs"][number]): string {
  return `${ref.role}|${ref.network}|${ref.txid.trim().toLowerCase()}`;
}

function pickRicherExecutionTxRef(
  current: SmartPayExecution["txRefs"][number],
  incoming: SmartPayExecution["txRefs"][number]
): SmartPayExecution["txRefs"][number] {
  const currentExplorer = current.explorerUrl?.trim() ?? "";
  const incomingExplorer = incoming.explorerUrl?.trim() ?? "";
  const currentRouteStepIndex = current.routeStepIndex ?? null;
  const incomingRouteStepIndex = incoming.routeStepIndex ?? null;
  if (currentRouteStepIndex === null && incomingRouteStepIndex !== null) {
    return incoming;
  }
  if (!currentExplorer && incomingExplorer) {
    return incoming;
  }
  return current;
}

function mergeExecutionTxRefs(
  primary: SmartPayExecution["txRefs"],
  secondary: SmartPayExecution["txRefs"]
): SmartPayExecution["txRefs"] {
  const merged = new Map<string, SmartPayExecution["txRefs"][number]>();

  for (const ref of [...primary, ...secondary]) {
    const key = getExecutionTxRefKey(ref);
    const existing = merged.get(key);
    merged.set(key, existing ? pickRicherExecutionTxRef(existing, ref) : ref);
  }

  return [...merged.values()];
}

function mergeReceiptTxRefs(
  primary: SmartPayReceipt["txRefs"],
  secondary: SmartPayReceipt["txRefs"]
): SmartPayReceipt["txRefs"] {
  const merged = new Map<string, SmartPayReceipt["txRefs"][number]>();

  for (const ref of [...primary, ...secondary]) {
    const key = getExecutionTxRefKey(ref);
    const existing = merged.get(key);
    merged.set(key, existing ? pickRicherExecutionTxRef(existing, ref) : ref);
  }

  return [...merged.values()];
}

function getReceiptNetworkFeeKey(fee: SmartPayReceipt["networkFees"][number]): string {
  return `${fee.network}|${fee.assetSymbol}|${fee.amount}`;
}

function mergeReceiptNetworkFees(
  primary: SmartPayReceipt["networkFees"],
  secondary: SmartPayReceipt["networkFees"]
): SmartPayReceipt["networkFees"] {
  const merged = new Map<string, SmartPayReceipt["networkFees"][number]>();

  for (const fee of [...primary, ...secondary]) {
    const key = getReceiptNetworkFeeKey(fee);
    if (!merged.has(key)) {
      merged.set(key, fee);
    }
  }

  return [...merged.values()];
}

function mergeReceiptRouteSummary(primary: string[], secondary: string[]): string[] {
  return Array.from(new Set([...primary, ...secondary]));
}

function mergeExecutionProgress(
  primary: SmartPayExecution["progress"] | null | undefined,
  secondary: SmartPayExecution["progress"] | null | undefined,
  status: SmartPayExecution["status"]
): SmartPayExecution["progress"] | null {
  if (!primary && !secondary) {
    return null;
  }

  const totalRouteSteps = Math.max(primary?.totalRouteSteps ?? 0, secondary?.totalRouteSteps ?? 0);
  const observedTxCount = Math.max(
    primary?.observedTxCount ?? 0,
    secondary?.observedTxCount ?? 0,
    status === "completed" ? totalRouteSteps : 0
  );
  const remainingRouteSteps = status === "completed"
    ? 0
    : Math.max(totalRouteSteps - observedTxCount, 0);
  const pendingRoles = status === "completed"
    ? []
    : Array.from(new Set([...(primary?.pendingRoles ?? []), ...(secondary?.pendingRoles ?? [])]));

  return {
    totalRouteSteps,
    observedTxCount,
    remainingRouteSteps,
    pendingRoles: remainingRouteSteps > 0 ? pendingRoles : [],
  };
}

function getRouteStepExecutionRole(
  step: SmartPayQuote["route"][number],
  index: number,
  totalSteps: number
): string {
  if (step.kind === "bridge") {
    return "bridge";
  }
  if (step.kind === "swap") {
    return "swap";
  }
  if (step.kind === "transfer" && totalSteps > 1 && index === totalSteps) {
    return "merchant_payout";
  }
  if (step.kind === "transfer") {
    return "payment";
  }
  return step.kind;
}

function isTxRefCompatibleWithRouteStep(
  candidate: SmartPayExecution["txRefs"][number],
  role: string,
  network: string
): boolean {
  const candidateRole = candidate.role?.trim();
  const candidateNetwork = candidate.network?.trim();

  if (candidateRole && candidateRole !== role) {
    return false;
  }
  if (candidateNetwork && candidateNetwork !== network) {
    return false;
  }

  return true;
}

function buildExecutionProgressFromQuote(
  quote: SmartPayQuote | null | undefined,
  txRefs: SmartPayExecution["txRefs"],
  status: SmartPayExecution["status"],
  fallback: SmartPayExecution["progress"] | null | undefined
): SmartPayExecution["progress"] | null {
  const route = quote?.route ?? [];
  if (route.length === 0) {
    return fallback ?? null;
  }

  const unmatchedRefs = [...txRefs];
  const matchedRouteRefs = route.map((step, index) => {
    const stepIndex = index + 1;
    const role = getRouteStepExecutionRole(step, stepIndex, route.length);
    const directIndexMatch = unmatchedRefs.findIndex(
      (candidate) =>
        candidate.routeStepIndex === stepIndex
        && isTxRefCompatibleWithRouteStep(candidate, role, step.network)
    );
    const roleNetworkMatch = unmatchedRefs.findIndex(
      (candidate) =>
        candidate.routeStepIndex == null
        && candidate.role === role
        && candidate.network === step.network
    );
    const matchIndex = directIndexMatch >= 0 ? directIndexMatch : roleNetworkMatch;
    return matchIndex >= 0 ? unmatchedRefs.splice(matchIndex, 1)[0] ?? null : null;
  });

  const observedTxCount = matchedRouteRefs.filter(Boolean).length;
  const pendingRoles = route.flatMap((step, index) => {
    if (matchedRouteRefs[index]) {
      return [];
    }
    return [getRouteStepExecutionRole(step, index + 1, route.length)];
  });

  if (status === "completed" && observedTxCount >= route.length) {
    return {
      totalRouteSteps: route.length,
      observedTxCount: route.length,
      remainingRouteSteps: 0,
      pendingRoles: [],
    };
  }

  return {
    totalRouteSteps: route.length,
    observedTxCount,
    remainingRouteSteps: Math.max(route.length - observedTxCount, 0),
    pendingRoles,
  };
}

function normalizeExecutionLifecycleFromQuote(
  quote: SmartPayQuote | null | undefined,
  execution: SmartPayExecution
): Pick<SmartPayExecution, "status" | "recoverable" | "nextAction" | "progress"> {
  if (execution.status === "failed") {
    return {
      status: execution.status,
      recoverable: execution.recoverable,
      nextAction: execution.nextAction ?? null,
      progress: buildExecutionProgressFromQuote(quote, execution.txRefs, execution.status, execution.progress),
    };
  }

  const progress = buildExecutionProgressFromQuote(quote, execution.txRefs, execution.status, execution.progress);
  const routeLength = quote?.route.length ?? 0;

  if (!progress || routeLength === 0) {
    return {
      status: execution.status,
      recoverable: execution.recoverable,
      nextAction: execution.nextAction ?? null,
      progress,
    };
  }

  if (execution.txRefs.length === 0) {
    return {
      status: "awaiting_local_signature",
      recoverable: true,
      nextAction: quote?.mode === "direct_send" ? "sign_direct_send_tx" : "sign_swap_tx",
      progress,
    };
  }

  if (progress.remainingRouteSteps > 0) {
    return {
      status: "pending_reconciliation",
      recoverable: true,
      nextAction: null,
      progress,
    };
  }

  return {
    status: "completed",
    recoverable: false,
    nextAction: null,
    progress: {
      ...progress,
      observedTxCount: routeLength,
      remainingRouteSteps: 0,
      pendingRoles: [],
    },
  };
}

function mergeExecutionPair(existing: SmartPayExecution, incoming: SmartPayExecution): SmartPayExecution {
  const preferIncoming = compareExecution(incoming, existing) >= 0;
  const preferred = preferIncoming ? incoming : existing;
  const fallback = preferIncoming ? existing : incoming;

  return {
    ...preferred,
    txRefs: mergeExecutionTxRefs(preferred.txRefs, fallback.txRefs),
    progress: mergeExecutionProgress(preferred.progress, fallback.progress, preferred.status),
    nextAction:
      preferred.status === "completed"
        ? null
        : preferred.nextAction ?? fallback.nextAction ?? null,
    error: preferred.error ?? fallback.error ?? null,
  };
}

function latestTimestamp(...values: Array<string | null | undefined>): string {
  const best = values.reduce<{ value: string | null; timestamp: number }>(
    (current, value) => {
      const timestamp = parseTimestamp(value);
      if (!value) return current;
      if (!current.value || timestamp > current.timestamp) {
        return { value, timestamp };
      }
      return current;
    },
    { value: null, timestamp: 0 }
  );
  return best.value ?? new Date(0).toISOString();
}

function normalizeOptionalSessionToken(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function normalizeSnapshotOrigin(
  origin: SmartPayHistoryEntry["snapshotOrigin"]
): SmartPayHistorySnapshotOrigin {
  switch (origin) {
    case "backend":
    case "local+backend":
    case "local":
      return origin;
    default:
      return "local";
  }
}

function normalizeFiniteInteger(value: unknown, minimum = 0): number | null {
  let numeric: number | null = null;

  if (typeof value === "number" && Number.isFinite(value)) {
    numeric = value;
  } else if (typeof value === "string") {
    const trimmed = value.trim();
    if (/^-?\d+$/.test(trimmed)) {
      numeric = Number.parseInt(trimmed, 10);
    }
  }

  if (numeric === null || !Number.isInteger(numeric) || numeric < minimum) {
    return null;
  }

  return numeric;
}

function inferSmartPayNetworkFromExplorerUrl(value: string): string | null {
  try {
    const url = new URL(value);
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
    if ((hostname === "ancap.cloud" || hostname.endsWith(".ancap.cloud")) && (pathname.includes("/acp/tx") || pathname.includes("/acp/transactions"))) {
      return "acp";
    }
  } catch {
    return null;
  }

  return null;
}

function normalizeHistoryTxRefs(
  refs: SmartPayExecution["txRefs"] | SmartPayReceipt["txRefs"] | unknown
): SmartPayExecution["txRefs"] {
  if (!Array.isArray(refs)) {
    return [];
  }

  return refs.flatMap((ref) => {
    if (!ref || typeof ref !== "object" || typeof (ref as { txid?: unknown }).txid !== "string") {
      return [];
    }

    const candidate = ref as {
      role?: unknown;
      network?: unknown;
      txid: string;
      explorerUrl?: unknown;
      routeStepIndex?: unknown;
    };
    const txid = candidate.txid.trim();
    if (!txid) {
      return [];
    }

    const explorerUrl = typeof candidate.explorerUrl === "string" ? candidate.explorerUrl.trim() : "";
    const normalizedNetwork = typeof candidate.network === "string" ? candidate.network.trim() : "";
    const routeStepIndex = normalizeFiniteInteger(candidate.routeStepIndex, 1);
    const normalizedRef: SmartPayExecution["txRefs"][number] = {
      role: typeof candidate.role === "string" ? candidate.role : "",
      network: normalizedNetwork || inferSmartPayNetworkFromExplorerUrl(explorerUrl) || "",
      txid,
      explorerUrl: explorerUrl || null,
    };

    if (routeStepIndex !== null) {
      normalizedRef.routeStepIndex = routeStepIndex;
    }

    return [normalizedRef];
  });
}

function normalizeExecutionProgress(
  progress: SmartPayExecution["progress"] | unknown
): SmartPayExecution["progress"] | null {
  if (!progress || typeof progress !== "object") {
    return null;
  }

  const candidate = progress as {
    totalRouteSteps?: unknown;
    observedTxCount?: unknown;
    remainingRouteSteps?: unknown;
    pendingRoles?: unknown;
  };

  return {
    totalRouteSteps: normalizeFiniteInteger(candidate.totalRouteSteps) ?? 0,
    observedTxCount: normalizeFiniteInteger(candidate.observedTxCount) ?? 0,
    remainingRouteSteps: normalizeFiniteInteger(candidate.remainingRouteSteps) ?? 0,
    pendingRoles: Array.isArray(candidate.pendingRoles)
      ? candidate.pendingRoles.filter((role): role is string => typeof role === "string" && role.trim().length > 0)
      : [],
  };
}

function normalizeQuoteSnapshot(quote: SmartPayQuote | null | undefined): SmartPayQuote | null {
  if (!quote || typeof quote !== "object") {
    return null;
  }

  return {
    ...quote,
    route: Array.isArray(quote.route) ? quote.route : [],
    networkFee: Array.isArray(quote.networkFee) ? quote.networkFee : [],
    warnings: Array.isArray(quote.warnings) ? quote.warnings : [],
    riskFlags: Array.isArray(quote.riskFlags) ? quote.riskFlags : [],
  };
}

function normalizeReceiptSnapshot(receipt: SmartPayReceipt | null | undefined): SmartPayReceipt | null {
  if (!receipt || typeof receipt !== "object") {
    return null;
  }

  return {
    ...receipt,
    routeSummary: Array.isArray(receipt.routeSummary)
      ? receipt.routeSummary.filter((value): value is string => typeof value === "string")
      : [],
    networkFees: Array.isArray(receipt.networkFees)
      ? receipt.networkFees.filter(
          (fee): fee is SmartPayReceipt["networkFees"][number] =>
            Boolean(
              fee
              && typeof fee === "object"
              && typeof (fee as { network?: unknown }).network === "string"
              && typeof (fee as { assetSymbol?: unknown }).assetSymbol === "string"
              && typeof (fee as { amount?: unknown }).amount === "string"
            )
        )
      : [],
    txRefs: normalizeHistoryTxRefs(receipt.txRefs),
  };
}

function normalizeExecutionSnapshot(execution: SmartPayExecution | null | undefined): SmartPayExecution | null {
  if (!execution || typeof execution !== "object" || !Array.isArray((execution as { txRefs?: unknown }).txRefs)) {
    return null;
  }

  return {
    ...execution,
    recoverable: Boolean(execution.recoverable),
    nextAction: typeof execution.nextAction === "string" ? execution.nextAction : null,
    progress: normalizeExecutionProgress(execution.progress),
    txRefs: normalizeHistoryTxRefs(execution.txRefs),
    error: typeof execution.error === "string" ? execution.error : null,
  };
}

function mergeSnapshotOrigin(
  first: SmartPayHistoryEntry["snapshotOrigin"],
  second: SmartPayHistoryEntry["snapshotOrigin"]
): SmartPayHistorySnapshotOrigin {
  const origins = new Set([normalizeSnapshotOrigin(first), normalizeSnapshotOrigin(second)]);
  if (origins.has("local+backend")) {
    return "local+backend";
  }
  if (origins.has("local") && origins.has("backend")) {
    return "local+backend";
  }
  if (origins.has("backend")) {
    return "backend";
  }
  return "local";
}

function normalizeHistoryEntry(entry: SmartPayHistoryEntry): SmartPayHistoryEntry | null {
  if (
    !entry
    || typeof entry.id !== "string"
    || !entry.id.trim()
    || typeof entry.savedAt !== "string"
    || !entry.savedAt.trim()
    || !entry.intent
    || typeof entry.intent !== "object"
    || typeof entry.intent.createdAt !== "string"
    || !entry.intent.asset
    || typeof entry.intent.asset !== "object"
    || !entry.intent.recipient
    || typeof entry.intent.recipient !== "object"
  ) {
    return null;
  }

  const execution = normalizeExecutionSnapshot(entry.execution);
  if (!execution) {
    return null;
  }

  const normalizedEntry: SmartPayHistoryEntry = {
    ...entry,
    quote: normalizeQuoteSnapshot(entry.quote),
    execution,
    receipt: normalizeReceiptSnapshot(entry.receipt),
    sessionToken: normalizeOptionalSessionToken(entry.sessionToken),
    snapshotOrigin: normalizeSnapshotOrigin(entry.snapshotOrigin),
  };
  const normalizedExecutionLifecycle = normalizeExecutionLifecycleFromQuote(
    normalizedEntry.quote,
    normalizedEntry.execution
  );

  return {
    ...normalizedEntry,
    execution: {
      ...normalizedEntry.execution,
      ...normalizedExecutionLifecycle,
    },
  };
}

function mergeReceiptPair(existing: SmartPayReceipt, incoming: SmartPayReceipt): SmartPayReceipt {
  const preferIncoming = compareReceipt(incoming, existing) >= 0;
  const preferred = preferIncoming ? incoming : existing;
  const fallback = preferIncoming ? existing : incoming;

  return {
    ...preferred,
    completedAt: latestTimestamp(preferred.completedAt, fallback.completedAt),
    sourceAssetSpent: preferred.sourceAssetSpent || fallback.sourceAssetSpent,
    sourceAmountSpent: preferred.sourceAmountSpent || fallback.sourceAmountSpent,
    targetAssetPaid: preferred.targetAssetPaid || fallback.targetAssetPaid,
    targetAmountPaid: preferred.targetAmountPaid || fallback.targetAmountPaid,
    serviceFeeAcp: preferred.serviceFeeAcp || fallback.serviceFeeAcp,
    recipientAddress: preferred.recipientAddress || fallback.recipientAddress,
    merchantLabel: preferred.merchantLabel ?? fallback.merchantLabel ?? null,
    routeSummary: mergeReceiptRouteSummary(preferred.routeSummary, fallback.routeSummary),
    networkFees: mergeReceiptNetworkFees(preferred.networkFees, fallback.networkFees),
    txRefs: mergeReceiptTxRefs(preferred.txRefs, fallback.txRefs),
  };
}

function mergeEntryPair(existing: SmartPayHistoryEntry, incoming: SmartPayHistoryEntry): SmartPayHistoryEntry {
  const preferIncoming = compareHistoryEntries(incoming, existing) >= 0;
  const preferred = preferIncoming ? incoming : existing;
  const fallback = preferIncoming ? existing : incoming;
  const quote = preferred.quote ?? fallback.quote ?? null;
  const execution = mergeExecutionPair(preferred.execution, fallback.execution);
  const normalizedLifecycle = normalizeExecutionLifecycleFromQuote(quote, execution);

  return {
    id: preferred.id,
    savedAt: latestTimestamp(
      preferred.savedAt,
      fallback.savedAt,
      preferred.execution.updatedAt,
      fallback.execution.updatedAt,
      preferred.receipt?.completedAt,
      fallback.receipt?.completedAt
    ),
    intent: preferred.intent,
    quote,
    execution: {
      ...execution,
      ...normalizedLifecycle,
    },
    receipt:
      preferred.receipt && fallback.receipt
        ? mergeReceiptPair(preferred.receipt, fallback.receipt)
        : preferred.receipt ?? fallback.receipt ?? null,
    sessionToken: preferred.sessionToken ?? fallback.sessionToken ?? null,
    snapshotOrigin: mergeSnapshotOrigin(preferred.snapshotOrigin, fallback.snapshotOrigin),
  };
}

export function mergeSmartPayActiveHistoryEntry(
  current: SmartPayHistoryEntry | null | undefined,
  incoming: SmartPayHistoryEntry
): SmartPayHistoryEntry {
  const normalizedIncoming = normalizeHistoryEntry({
    ...incoming,
    snapshotOrigin: incoming.snapshotOrigin ?? "local",
  });

  if (!normalizedIncoming) {
    return {
      ...incoming,
      snapshotOrigin: incoming.snapshotOrigin ?? "local",
    };
  }

  const normalizedCurrent = current ? normalizeHistoryEntry(current) : null;
  if (!normalizedCurrent || normalizedCurrent.id !== normalizedIncoming.id) {
    return normalizedIncoming;
  }

  return mergeEntryPair(normalizedCurrent, normalizedIncoming);
}

export function compareHistoryEntries(a: SmartPayHistoryEntry, b: SmartPayHistoryEntry): number {
  const timestampDiff = entryTimestamp(a) - entryTimestamp(b);
  if (timestampDiff !== 0) return timestampDiff;

  const receiptDiff = receiptScore(a.receipt ?? null) - receiptScore(b.receipt ?? null);
  if (receiptDiff !== 0) return receiptDiff;

  return executionScore(a.execution) - executionScore(b.execution);
}

export function mergeSmartPayHistoryEntries(
  entries: SmartPayHistoryEntry[],
  limit = MAX_HISTORY_ITEMS
): SmartPayHistoryEntry[] {
  const merged = new Map<string, SmartPayHistoryEntry>();

  for (const entry of entries) {
    const normalizedEntry = normalizeHistoryEntry(entry);
    if (!normalizedEntry) {
      continue;
    }
    const existing = merged.get(normalizedEntry.id);
    merged.set(normalizedEntry.id, existing ? mergeEntryPair(existing, normalizedEntry) : normalizedEntry);
  }

  return [...merged.values()]
    .sort((a, b) => compareHistoryEntries(b, a))
    .slice(0, limit);
}

export function buildSmartPayRemoteHistoryEntries(
  payments: SmartPayApiHistoryEntry[]
): SmartPayHistoryEntry[] {
  return payments
    .filter((item) => item?.execution?.id && item?.paymentIntent && item?.quote)
    .map((item) => ({
      id: item.execution.id,
      savedAt:
        item.execution.updatedAt ??
        item.execution.createdAt ??
        item.receipt?.completedAt ??
        item.paymentIntent.createdAt,
      intent: item.paymentIntent,
      quote: item.quote,
      execution: item.execution,
      receipt: item.receipt ?? null,
      sessionToken: null,
      snapshotOrigin: "backend",
    }));
}

export function mergeSmartPayHistoryWithRemotePayments(
  localHistory: SmartPayHistoryEntry[],
  remotePayments: SmartPayApiHistoryEntry[],
  limit = MAX_HISTORY_ITEMS
): SmartPayHistoryEntry[] {
  return mergeSmartPayHistoryEntries(
    [...buildSmartPayRemoteHistoryEntries(remotePayments), ...localHistory],
    limit
  );
}

function normalizeHistory(payload: PersistedSmartPayHistory | null): PersistedSmartPayHistory {
  if (!payload || payload.version !== 1 || !Array.isArray(payload.entries)) {
    return { version: 1, entries: [] };
  }
  return {
    version: 1,
    entries: mergeSmartPayHistoryEntries(payload.entries),
  };
}

async function persistHistoryEntries(entries: SmartPayHistoryEntry[]): Promise<SmartPayHistoryEntry[]> {
  const next = mergeSmartPayHistoryEntries(entries);
  const payload: PersistedSmartPayHistory = {
    version: 1,
    entries: next,
  };
  await SecureStore.setItemAsync(KEY_SMART_PAY_HISTORY, JSON.stringify(payload), STORE_OPTIONS);
  return next;
}

export async function loadSmartPayHistory(): Promise<SmartPayHistoryEntry[]> {
  const raw = await SecureStore.getItemAsync(KEY_SMART_PAY_HISTORY, STORE_OPTIONS);
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw) as PersistedSmartPayHistory;
    return normalizeHistory(parsed).entries;
  } catch {
    await clearSmartPayHistory();
    return [];
  }
}

export async function saveSmartPayHistoryEntry(entry: SmartPayHistoryEntry): Promise<SmartPayHistoryEntry[]> {
  const existing = await loadSmartPayHistory();
  return persistHistoryEntries([
    {
      ...entry,
      snapshotOrigin: entry.snapshotOrigin ?? "local",
    },
    ...existing,
  ]);
}

export async function replaceSmartPayHistoryEntries(entries: SmartPayHistoryEntry[]): Promise<SmartPayHistoryEntry[]> {
  return persistHistoryEntries(entries);
}

export async function clearSmartPayHistory(): Promise<void> {
  await SecureStore.deleteItemAsync(KEY_SMART_PAY_HISTORY, STORE_OPTIONS);
}

export async function loadSmartPayHistoryTimeline(
  options: SmartPayHistoryLoadOptions = {}
): Promise<SmartPayHistoryEntry[]> {
  const limit = options.limit ?? MAX_HISTORY_ITEMS;
  const localHistory = await loadSmartPayHistory();

  if (!options.hasAccountAuth || !options.listRemoteHistory) {
    return localHistory.slice(0, limit);
  }

  try {
    const remotePayments = await options.listRemoteHistory(limit);
    return mergeSmartPayHistoryWithRemotePayments(localHistory, remotePayments, limit);
  } catch {
    return localHistory.slice(0, limit);
  }
}

export async function clearSmartPayHistorySnapshots(
  options: SmartPayHistoryClearOptions = {}
): Promise<SmartPayHistoryEntry[]> {
  const limit = options.limit ?? MAX_HISTORY_ITEMS;
  await clearSmartPayHistory();

  if (!options.hasAccountAuth || !options.listRemoteHistory) {
    return [];
  }

  try {
    const remotePayments = await options.listRemoteHistory(limit);
    return mergeSmartPayHistoryWithRemotePayments([], remotePayments, limit);
  } catch {
    return [];
  }
}
