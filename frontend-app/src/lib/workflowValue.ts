export type AssessmentVerdict = "accepted" | "revision_requested" | "rejected";
export type WorkflowAssessment = {
  id: string; workflow_run_id: string; result_hash: string; verdict: AssessmentVerdict;
  baseline_minutes: string | null; assisted_minutes: string | null;
  hourly_rate: string | null; hourly_currency: string | null; note: string | null; created_at: string;
};
export type AssessmentState = { result_hash: string; assessment: WorkflowAssessment | null; has_stale_assessment: boolean };
export type AssessmentInput = {
  result_hash: string; verdict: AssessmentVerdict; baseline_minutes: string | null; assisted_minutes: string | null;
  hourly_rate: string | null; hourly_currency: string | null; note: string | null;
};
export type ValueSummary = {
  days: number; limit: number; truncated: boolean; window_start: string; window_end: string;
  completed_count: number; assessed_count: number; accepted_count: number; revision_requested_count: number; rejected_count: number;
  timed_assessment_count: number; labor_valued_count: number; estimated_minutes_saved: string | null;
  estimated_labor_value: { amount: string; currency: string }[]; ledger_charges: { amount: string; currency: string }[];
  estimates_are_self_reported: true;
  ledger_charges_are_verified_external_payments: false;
  scope_basis: "completed_runs_created_in_window";
};

export function formatValueEstimate(value: string | null, language: string): string | null {
  if (value === null || value.trim() === "" || !Number.isFinite(Number(value))) return null;
  return new Intl.NumberFormat(language, { maximumFractionDigits: 2 }).format(Number(value));
}

export type AssessmentHistory = { items: WorkflowAssessment[]; has_more: boolean };
export type AssessedResult = { assessment_id: string; result_hash: string; result: unknown };
