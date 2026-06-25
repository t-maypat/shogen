import type { CampaignBrief } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface ApiEnvelope<T> {
  data: T | null;
  error: { code: string; message: string; details?: unknown } | null;
}

export interface CampaignSummaryResponse {
  id: string;
  tenant_id: string;
  name: string;
  status: string;
  brief: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface WorkflowRunResponse {
  id: string;
  status: string;
  current_stage: string | null;
  revision_count: number;
  replay_mode: boolean;
  error: { message?: string; type?: string } & Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreativeVariantResponse {
  id: string;
  run_id: string;
  client_variant_id: string;
  persona_id: string;
  channel: string;
  journey_stage: string;
  primary_kpi: string;
  revision_number: number;
  status: string;
  claims: string[];
  disclosure: string | null;
  copy: Record<string, unknown>;
  parent_variant_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface PolicyFindingResponse {
  id: string;
  variant_id: string;
  source: string;
  rule_id: string | null;
  severity: string;
  status: string;
  finding_type: string;
  evidence: string;
  message: string;
  suggestion: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  resolved_at: string | null;
}

export interface EvaluationResultResponse {
  id: string;
  variant_id: string;
  persona_id: string;
  channel: string;
  scores: Record<string, number>;
  total_score: string;
  created_at: string;
}

export interface WaveProposalResponse {
  id: string;
  proposal: Record<string, unknown>;
  rationale: Record<string, unknown>;
  created_at: string;
}

export interface EventLogResponse {
  id: number;
  run_id: string | null;
  event_type: string;
  stage: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface CampaignStateResponse {
  campaign: CampaignSummaryResponse;
  latest_run: WorkflowRunResponse | null;
  strategy: Record<string, unknown> | null;
  journey: Record<string, unknown> | null;
  mock_deployment: Record<string, unknown> | null;
  creative_variants: CreativeVariantResponse[];
  policy_findings: PolicyFindingResponse[];
  approval: Record<string, unknown> | null;
  evaluation_results: EvaluationResultResponse[];
  wave_proposal: WaveProposalResponse | null;
  events: EventLogResponse[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const envelope = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || envelope.error || !envelope.data) {
    throw new Error(envelope.error?.message ?? "Shogun could not complete the request.");
  }
  return envelope.data;
}

export const api = {
  createCampaign: (brief: CampaignBrief) =>
    request<{ campaign_id: string; status: string }>("/api/campaigns", {
      method: "POST",
      body: JSON.stringify({
        name: brief.campaignName,
        brief: {
          product_name: brief.productName,
          product_category: brief.productCategory,
          objective: brief.objective,
          audience_summary: brief.audienceSummary,
          budget_range: brief.budgetRange,
          duration_days: brief.durationDays,
          brand_voice: brief.brandVoice,
          required_claims: brief.requiredClaims,
          risky_claims: brief.riskyClaims,
          channels: brief.channels,
        },
      }),
    }),
  getCampaign: (id: string) => request<CampaignStateResponse>(`/api/campaigns/${id}`),
  runCampaign: (id: string, mode: "live" | "replay") =>
    request<{ run_id: string; status: string }>(`/api/campaigns/${id}/run`, {
      method: "POST",
      body: JSON.stringify({ mode }),
    }),
  approveCampaign: (id: string) =>
    request<{ approval_id: string; status: string }>(`/api/campaigns/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved_by: "Demo Marketer", notes: "Approved for mock deployment." }),
    }),
  startReplay: () =>
    request<{ campaign_id: string; run_id: string; status: string; replay_mode: boolean }>(
      "/api/demo/replay",
      { method: "POST", body: JSON.stringify({ scenario: "fintech" }) },
    ),
};

export { API_BASE_URL };
