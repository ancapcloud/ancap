export interface RevenueWorkflow {
  workflow_slug: string;
  currency: string;
  captured_amount?: string;
}

/** Rank only comparable ledger amounts; never add or rank across currencies. */
export function topWorkflowsByCurrency<T extends RevenueWorkflow>(rows: T[], limit = 10): { currency: string; items: T[] }[] {
  const groups = new Map<string, T[]>();
  for (const row of rows) {
    const items = groups.get(row.currency) || [];
    items.push(row);
    groups.set(row.currency, items);
  }
  return Array.from(groups, ([currency, items]) => ({
    currency,
    items: items.sort((a, b) => Number(b.captured_amount || "0") - Number(a.captured_amount || "0") || a.workflow_slug.localeCompare(b.workflow_slug)).slice(0, limit),
  })).sort((a, b) => a.currency.localeCompare(b.currency));
}
