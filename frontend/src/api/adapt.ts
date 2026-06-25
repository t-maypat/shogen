import { completedStages } from "../data/demo";
import type {
  AllocationChange,
  CampaignStatus,
  Channel,
  CreativeCopy,
  CreativeVariant,
  EvaluationScore,
  JourneyStep,
  KPI,
  Persona,
  PolicyFinding,
  WorkflowStage,
} from "../types";
import type {
  CampaignStateResponse,
  CreativeVariantResponse,
  EvaluationResultResponse,
  EventLogResponse,
  PolicyFindingResponse,
  WaveProposalResponse,
  WorkflowRunResponse,
} from "./client";

const ACCENTS = ["#e56848", "#2f7d67", "#5f6db5"];

interface RawKpi {
  id: string;
  label: string;
  reason: string;
}

interface RawPersona {
  id: string;
  name: string;
  summary: string;
  needs: string[];
  objections: string[];
  preferred_tone: string;
  decision_trigger: string;
  risk_sensitivity: Persona["riskSensitivity"];
}

interface RawJourneyStep {
  id: string;
  persona_id: string;
  channel: Channel;
  journey_stage: JourneyStep["journeyStage"];
  objective: string;
  primary_kpi_id: string;
  allocation_percent: number;
  message_angle: string;
}

export function adaptKpis(strategy: Record<string, unknown> | null): KPI[] {
  if (strategy == null) return [];
  const kpis = (strategy.kpis as RawKpi[] | undefined) ?? [];
  return kpis.map((kpi) => ({
    id: kpi.id,
    name: kpi.label,
    targetDirection: "increase",
    measurement: kpi.reason,
    rationale: kpi.reason,
    target: "",
  }));
}

export function adaptPersonas(strategy: Record<string, unknown> | null): Persona[] {
  if (strategy == null) return [];
  const personas = (strategy.personas as RawPersona[] | undefined) ?? [];
  return personas.map((persona, index) => ({
    id: persona.id,
    name: persona.name,
    shortName: persona.name.split(" ")[0],
    summary: persona.summary,
    needs: persona.needs,
    objections: persona.objections,
    preferredTone: persona.preferred_tone,
    decisionTrigger: persona.decision_trigger,
    riskSensitivity: persona.risk_sensitivity,
    accent: ACCENTS[index % ACCENTS.length],
  }));
}

export function adaptJourney(journey: Record<string, unknown> | null): JourneyStep[] {
  if (journey == null) return [];
  const steps = (journey.steps as RawJourneyStep[] | undefined) ?? [];
  return steps.map((step) => ({
    id: step.id,
    personaId: step.persona_id,
    channel: step.channel,
    journeyStage: step.journey_stage,
    objective: step.objective,
    primaryKpiId: step.primary_kpi_id,
    allocationPercent: step.allocation_percent,
    messageAngle: step.message_angle,
  }));
}

const baseId = (v: { persona_id: string; channel: string }) => `${v.persona_id}_${v.channel}`;

export function buildUuidToBaseId(variants: CreativeVariantResponse[]): Record<string, string> {
  return Object.fromEntries(variants.map((variant) => [variant.id, baseId(variant)]));
}

function adaptCopy(channel: string, copy: Record<string, unknown>): CreativeCopy {
  if (channel === "google_search") {
    return {
      type: "google",
      headlines: (copy.headlines as string[] | undefined) ?? [],
      descriptions: (copy.descriptions as string[] | undefined) ?? [],
      path: (copy.path as string | null | undefined) ?? "",
      cta: (copy.cta as string | undefined) ?? "",
    };
  }
  if (channel === "linkedin_sponsored_post") {
    return {
      type: "linkedin",
      introText: (copy.intro_text as string | undefined) ?? "",
      headline: (copy.headline as string | undefined) ?? "",
      description: (copy.description as string | undefined) ?? "",
      cta: (copy.cta as string | undefined) ?? "",
    };
  }
  return {
    type: "email",
    subject: (copy.subject as string | undefined) ?? "",
    preheader: (copy.preheader as string | undefined) ?? "",
    body: (copy.body as string | undefined) ?? "",
    cta: (copy.cta as string | undefined) ?? "",
  };
}

function representativeLine(channel: string, copy: Record<string, unknown>): string {
  if (channel === "google_search") return ((copy.descriptions as string[] | undefined) ?? [])[0] ?? "";
  if (channel === "linkedin_sponsored_post") return (copy.intro_text as string | undefined) ?? "";
  return (copy.subject as string | undefined) ?? "";
}

const VARIANT_STATUS_MAP: Record<string, CreativeVariant["status"]> = {
  passed: "policy_ready",
  generated: "policy_ready",
  revised: "policy_ready",
  warning: "warning",
  blocked: "blocked",
};

export function adaptVariants(variants: CreativeVariantResponse[]): CreativeVariant[] {
  const groups = new Map<string, CreativeVariantResponse[]>();
  for (const variant of variants) {
    const id = baseId(variant);
    const group = groups.get(id);
    if (group) {
      group.push(variant);
    } else {
      groups.set(id, [variant]);
    }
  }

  return Array.from(groups.entries()).map(([id, group]) => {
    const sorted = [...group].sort((a, b) => a.revision_number - b.revision_number);
    const leaf = sorted[sorted.length - 1];
    const original = sorted[0];
    return {
      id,
      personaId: leaf.persona_id,
      channel: leaf.channel as Channel,
      journeyStage: leaf.journey_stage,
      primaryKpiId: leaf.primary_kpi,
      claims: leaf.claims,
      disclosure: leaf.disclosure ?? "",
      copy: adaptCopy(leaf.channel, leaf.copy),
      status: VARIANT_STATUS_MAP[leaf.status] ?? "warning",
      revision: leaf.revision_number,
      previousCopy: sorted.length > 1 ? representativeLine(original.channel, original.copy) : undefined,
    };
  });
}

const FINDING_SOURCE_MAP: Record<string, PolicyFinding["source"]> = {
  deterministic: "deterministic",
  semantic: "semantic_ai",
};

export function adaptFindings(
  findings: PolicyFindingResponse[],
  uuidToBaseId: Record<string, string>,
): PolicyFinding[] {
  return findings.map((finding) => ({
    id: finding.id,
    variantId: uuidToBaseId[finding.variant_id] ?? finding.variant_id,
    source: FINDING_SOURCE_MAP[finding.source] ?? "deterministic",
    ruleId: finding.rule_id ?? undefined,
    severity: finding.severity as PolicyFinding["severity"],
    findingType: finding.finding_type,
    evidence: finding.evidence,
    message: finding.message,
    suggestion: finding.suggestion ?? undefined,
    resolved: finding.resolved_at != null || finding.status === "resolved",
  }));
}

export function adaptEvaluation(
  results: EvaluationResultResponse[],
  uuidToBaseId: Record<string, string>,
): EvaluationScore[] {
  return results.map((result) => ({
    variantId: uuidToBaseId[result.variant_id] ?? result.variant_id,
    personaId: result.persona_id,
    channel: result.channel as Channel,
    messageFit: result.scores.message_fit,
    channelFit: result.scores.channel_fit,
    ctaClarity: result.scores.cta_clarity,
    policyQuality: result.scores.policy_quality,
    journeyConsistency: result.scores.journey_consistency,
    weightedTotal: Number(result.total_score),
    rationale: "",
  }));
}

export interface Wave2Rewrite {
  variant_id: string;
  client_variant_id: string;
  rewritten_copy: Record<string, unknown>;
  rationale: string;
}

export interface Wave2Rationale {
  rationale: string;
  allocation_summary: string[];
  method: string;
  directional: boolean;
}

export interface AdaptedWave2 {
  allocationChanges: AllocationChange[];
  rewrites: Wave2Rewrite[];
  rationale: Wave2Rationale | null;
}

interface RawAllocationChange {
  persona_id: string;
  channel: Channel;
  wave1_allocation_percent: number;
  wave2_allocation_percent: number;
  reason_codes: string[];
}

export function adaptWave2(waveProposal: WaveProposalResponse | null): AdaptedWave2 {
  if (waveProposal == null) {
    return { allocationChanges: [], rewrites: [], rationale: null };
  }
  const changes = (waveProposal.proposal.allocation_changes as RawAllocationChange[] | undefined) ?? [];
  return {
    allocationChanges: changes.map((change) => ({
      personaId: change.persona_id,
      channel: change.channel,
      wave1: change.wave1_allocation_percent,
      wave2: change.wave2_allocation_percent,
      reasonCode: change.reason_codes.join(", "),
    })),
    rewrites: (waveProposal.proposal.rewrites as Wave2Rewrite[] | undefined) ?? [],
    rationale: (waveProposal.rationale as unknown as Wave2Rationale) ?? null,
  };
}

const STAGE_TO_NODE: Record<string, string> = {
  strategy: "strategy",
  journey: "journey",
  creative: "creative",
  policy: "policy",
  approval_required: "approval",
  approval: "approval",
  mock_deployment: "deploy",
  evaluation: "evaluation",
  wave2: "wave2",
};

export const STAGE_TEMPLATE: WorkflowStage[] = completedStages.map((stage) => ({
  ...stage,
  status: stage.id === "brief" ? "completed" : "pending",
}));

export function deriveStages(
  latestRun: WorkflowRunResponse | null,
  events: EventLogResponse[],
): WorkflowStage[] {
  const stages = STAGE_TEMPLATE.map((stage) => ({ ...stage }));
  const byId = new Map(stages.map((stage) => [stage.id, stage]));
  const setStatus = (nodeId: string | undefined, status: WorkflowStage["status"]) => {
    const stage = nodeId ? byId.get(nodeId) : undefined;
    if (stage) stage.status = status;
  };

  for (const event of events) {
    const nodeId = event.stage ? STAGE_TO_NODE[event.stage] : undefined;
    switch (event.event_type) {
      case "stage.started":
        setStatus(nodeId, "running");
        break;
      case "stage.completed":
        setStatus(nodeId, "completed");
        if (event.stage === "policy") setStatus("semantic", "completed");
        break;
      case "approval.required":
        setStatus("approval", "approval_required");
        break;
      case "mock_deployment.completed":
        setStatus("deploy", "completed");
        break;
      case "evaluation.completed":
        setStatus("evaluation", "completed");
        break;
      case "wave2.completed":
        setStatus("wave2", "completed");
        break;
      case "policy.failed":
        setStatus("policy", "failed");
        setStatus("semantic", "failed");
        break;
      case "workflow.failed":
        setStatus(nodeId, "failed");
        break;
      default:
        break;
    }
  }

  if ((latestRun?.revision_count ?? 0) > 0) {
    if (byId.get("policy")?.status === "completed") setStatus("policy", "warning");
    if (byId.get("semantic")?.status === "completed") setStatus("semantic", "warning");
  }

  return stages;
}

export interface AdaptedLatestRun {
  status: string | null;
  currentStage: string | null;
  replayMode: boolean;
  error: WorkflowRunResponse["error"] | null;
  revisionCount: number;
}

export interface AdaptedCampaignState {
  status: CampaignStatus;
  kpis: KPI[];
  personas: Persona[];
  journey: JourneyStep[];
  variants: CreativeVariant[];
  findings: PolicyFinding[];
  evaluation: EvaluationScore[];
  wave2: AdaptedWave2;
  stages: WorkflowStage[];
  latestRun: AdaptedLatestRun | null;
}

export function adaptCampaignState(raw: CampaignStateResponse): AdaptedCampaignState {
  const uuidToBaseId = buildUuidToBaseId(raw.creative_variants);
  return {
    status: raw.campaign.status as CampaignStatus,
    kpis: adaptKpis(raw.strategy),
    personas: adaptPersonas(raw.strategy),
    journey: adaptJourney(raw.journey),
    variants: adaptVariants(raw.creative_variants),
    findings: adaptFindings(raw.policy_findings, uuidToBaseId),
    evaluation: adaptEvaluation(raw.evaluation_results, uuidToBaseId),
    wave2: adaptWave2(raw.wave_proposal),
    stages: deriveStages(raw.latest_run, raw.events),
    latestRun: raw.latest_run
      ? {
          status: raw.latest_run.status,
          currentStage: raw.latest_run.current_stage,
          replayMode: raw.latest_run.replay_mode,
          error: raw.latest_run.error,
          revisionCount: raw.latest_run.revision_count,
        }
      : null,
  };
}
