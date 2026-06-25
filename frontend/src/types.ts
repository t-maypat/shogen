export type Channel = "google_search" | "linkedin_sponsored_post" | "email";

export type CampaignStatus =
  | "draft"
  | "running"
  | "approval_required"
  | "approved"
  | "evaluating"
  | "completed"
  | "failed";

export type StageStatus =
  | "pending"
  | "running"
  | "completed"
  | "warning"
  | "failed"
  | "approval_required";

export type TabId = "brief" | "journey" | "creative" | "results";

export type ConnectionState = "idle" | "live" | "reconnecting" | "error";

export interface CampaignBrief {
  campaignName: string;
  productName: string;
  productCategory: string;
  objective: string;
  audienceSummary: string;
  budgetRange: string;
  durationDays: number;
  brandVoice: string[];
  requiredClaims: string[];
  riskyClaims: string[];
  channels: Channel[];
}

export interface KPI {
  id: string;
  name: string;
  targetDirection: "increase" | "decrease" | "maintain";
  measurement: string;
  rationale: string;
  target: string;
}

export interface Persona {
  id: string;
  name: string;
  shortName: string;
  summary: string;
  needs: string[];
  objections: string[];
  preferredTone: string;
  decisionTrigger: string;
  riskSensitivity: "low" | "medium" | "high";
  accent: string;
}

export interface JourneyStep {
  id: string;
  personaId: string;
  channel: Channel;
  journeyStage: "discovery" | "consideration" | "nurture" | "conversion";
  objective: string;
  primaryKpiId: string;
  allocationPercent: number;
  messageAngle: string;
}

export interface GoogleCopy {
  type: "google";
  headlines: string[];
  descriptions: string[];
  path: string;
  cta: string;
}

export interface LinkedInCopy {
  type: "linkedin";
  introText: string;
  headline: string;
  description: string;
  cta: string;
}

export interface EmailCopy {
  type: "email";
  subject: string;
  preheader: string;
  body: string;
  cta: string;
}

export type CreativeCopy = GoogleCopy | LinkedInCopy | EmailCopy;

export interface CreativeVariant {
  id: string;
  personaId: string;
  channel: Channel;
  journeyStage: string;
  primaryKpiId: string;
  claims: string[];
  disclosure: string;
  copy: CreativeCopy;
  status: "policy_ready" | "warning" | "blocked";
  revision: number;
  previousCopy?: string;
}

export interface PolicyFinding {
  id: string;
  variantId: string;
  source: "deterministic" | "semantic_ai";
  ruleId?: string;
  severity: "blocking" | "high" | "medium" | "low" | "info";
  findingType: string;
  evidence: string;
  message: string;
  suggestion?: string;
  resolved: boolean;
}

export interface EvaluationScore {
  variantId: string;
  personaId: string;
  channel: Channel;
  messageFit: number;
  channelFit: number;
  ctaClarity: number;
  policyQuality: number;
  journeyConsistency: number;
  weightedTotal: number;
  rationale: string;
}

export interface AllocationChange {
  personaId: string;
  channel: Channel;
  wave1: number;
  wave2: number;
  reasonCode: string;
}

export interface WorkflowStage {
  id: string;
  label: string;
  eyebrow: string;
  status: StageStatus;
  summary: string;
}

export interface WorkflowEvent {
  campaignId: string;
  runId: string;
  eventType: string;
  stage?: string;
  status: string;
  timestamp: string;
  display?: Record<string, unknown>;
}
