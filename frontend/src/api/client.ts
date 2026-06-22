import type { CampaignBrief } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface ApiEnvelope<T> {
  data: T | null;
  error: { code: string; message: string; details?: unknown } | null;
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
  getCampaign: (id: string) => request<unknown>(`/api/campaigns/${id}`),
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
