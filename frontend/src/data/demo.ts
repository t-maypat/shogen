import type {
  AllocationChange,
  CampaignBrief,
  CreativeVariant,
  EvaluationScore,
  JourneyStep,
  KPI,
  Persona,
  PolicyFinding,
  WorkflowStage,
} from "../types";

export const demoBrief: CampaignBrief = {
  campaignName: "NestWise · Summer acquisition",
  productName: "NestWise",
  productCategory: "Fintech savings and starter investing app",
  objective: "Drive qualified signups for a beginner-friendly savings and investing account.",
  audienceSummary:
    "Young first-time investors, risk-conscious professionals, and small-business owners who want a clearer way to build financial habits.",
  budgetRange: "$25k demo budget",
  durationDays: 30,
  brandVoice: ["Clear", "Trustworthy", "Encouraging", "Responsible"],
  requiredClaims: ["Easy onboarding", "Beginner-friendly saving tools"],
  riskyClaims: ["guaranteed returns"],
  channels: ["google_search", "linkedin_sponsored_post", "email"],
};

export const blankBrief: CampaignBrief = {
  campaignName: "",
  productName: "",
  productCategory: "",
  objective: "",
  audienceSummary: "",
  budgetRange: "",
  durationDays: 30,
  brandVoice: [],
  requiredClaims: [],
  riskyClaims: [],
  channels: ["google_search", "linkedin_sponsored_post", "email"],
};

export const kpis: KPI[] = [
  {
    id: "kpi1",
    name: "Qualified signup intent",
    targetDirection: "increase",
    measurement: "Completed onboarding starts",
    rationale: "Keeps the campaign focused on meaningful consideration, not empty clicks.",
    target: "+18%",
  },
  {
    id: "kpi2",
    name: "Message relevance",
    targetDirection: "increase",
    measurement: "Persona-message fit score",
    rationale: "Tests whether each audience sees a reason to care that matches their needs.",
    target: "≥ 82",
  },
  {
    id: "kpi3",
    name: "Policy readiness",
    targetDirection: "maintain",
    measurement: "Variants without blocking findings",
    rationale: "Maintains a reviewable, responsible creative set before any real spend.",
    target: "100%",
  },
];

export const personas: Persona[] = [
  {
    id: "p1",
    name: "Maya · First-time builder",
    shortName: "Maya",
    summary: "A 26-year-old professional ready to start investing, but wary of complexity and jargon.",
    needs: ["A small first step", "Plain-language guidance"],
    objections: ["Fear of choosing wrong", "Unclear fees"],
    preferredTone: "Encouraging and direct",
    decisionTrigger: "A low-pressure, guided way to begin",
    riskSensitivity: "high",
    accent: "#e56848",
  },
  {
    id: "p2",
    name: "Arjun · Careful optimizer",
    shortName: "Arjun",
    summary: "A 35-year-old professional balancing long-term goals with a cautious approach to risk.",
    needs: ["Transparent choices", "Evidence of control"],
    objections: ["Hype-driven claims", "Opaque products"],
    preferredTone: "Measured and credible",
    decisionTrigger: "Control, transparency, and habit-building",
    riskSensitivity: "high",
    accent: "#2f7d67",
  },
  {
    id: "p3",
    name: "Leena · Business balancer",
    shortName: "Leena",
    summary: "A small-business owner separating business volatility from personal financial progress.",
    needs: ["Flexible routines", "Simple progress view"],
    objections: ["Rigid commitments", "Time-consuming setup"],
    preferredTone: "Practical and efficient",
    decisionTrigger: "A plan that works around an irregular month",
    riskSensitivity: "medium",
    accent: "#5f6db5",
  },
];

const allocations = [15, 12, 10, 13, 12, 10, 10, 9, 9];
const stages: JourneyStep["journeyStage"][] = ["discovery", "consideration", "nurture"];
const channelOrder = ["google_search", "linkedin_sponsored_post", "email"] as const;
const angles = [
  ["Start with one clear step", "Confidence without the finance-speak", "A gentle plan for your first month"],
  ["Build a plan you can inspect", "Progress over promises", "Keep your money habits on your terms"],
  ["Make uneven months work", "A calmer personal finance system", "Small routines that flex with business"],
];

export const journeySteps: JourneyStep[] = personas.flatMap((persona, personaIndex) =>
  channelOrder.map((channel, channelIndex) => ({
    id: `journey-${persona.id}-${channel}`,
    personaId: persona.id,
    channel,
    journeyStage: stages[channelIndex],
    objective: channelIndex === 0 ? "Capture active intent" : channelIndex === 1 ? "Build informed trust" : "Nurture a confident next step",
    primaryKpiId: channelIndex === 2 ? "kpi1" : channelIndex === 1 ? "kpi2" : "kpi1",
    allocationPercent: allocations[personaIndex * 3 + channelIndex],
    messageAngle: angles[personaIndex][channelIndex],
  })),
);

function googleVariant(id: string, personaId: string, headline: string, description: string): CreativeVariant {
  return {
    id,
    personaId,
    channel: "google_search",
    journeyStage: "discovery",
    primaryKpiId: "kpi1",
    claims: ["Beginner-friendly saving tools"],
    disclosure: "Investing involves risk. Returns are not guaranteed.",
    status: "policy_ready",
    revision: personaId === "p1" ? 1 : 0,
    previousCopy: personaId === "p1" ? "Start investing today with guaranteed returns." : undefined,
    copy: {
      type: "google",
      headlines: [headline, "Build better money habits", "Start at your own pace"],
      descriptions: [description, "Clear tools. Flexible saving. No finance-speak required."],
      path: "nestwise.app/start",
      cta: "Start building",
    },
  };
}

function linkedInVariant(id: string, personaId: string, introText: string, headline: string): CreativeVariant {
  return {
    id,
    personaId,
    channel: "linkedin_sponsored_post",
    journeyStage: "consideration",
    primaryKpiId: "kpi2",
    claims: ["Easy onboarding"],
    disclosure: "Investing involves risk. Returns are not guaranteed.",
    status: personaId === "p3" ? "warning" : "policy_ready",
    revision: 0,
    copy: {
      type: "linkedin",
      introText,
      headline,
      description: "Beginner-friendly saving and investing tools, built around your pace.",
      cta: "Learn more",
    },
  };
}

function emailVariant(id: string, personaId: string, subject: string, body: string): CreativeVariant {
  return {
    id,
    personaId,
    channel: "email",
    journeyStage: "nurture",
    primaryKpiId: "kpi1",
    claims: ["Easy onboarding", "Beginner-friendly saving tools"],
    disclosure: "Investing involves risk. Returns are not guaranteed.",
    status: "policy_ready",
    revision: 0,
    copy: {
      type: "email",
      subject,
      preheader: "A practical next step, shaped around you.",
      body,
      cta: "Build my plan",
    },
  };
}

export const variants: CreativeVariant[] = [
  googleVariant("v1", "p1", "Your first step, made clear", "Start a simple saving routine and learn as you go with NestWise."),
  linkedInVariant("v2", "p1", "You do not need to become a market expert before you start building a better money habit.", "A clearer way to begin"),
  emailVariant("v3", "p1", "Your first month can start small", "Hi Maya,\n\nThere is no perfect first move. NestWise helps you set a comfortable saving rhythm, understand each choice, and adjust as you learn. Start with a plan that feels like yours."),
  googleVariant("v4", "p2", "A plan without the hype", "Build disciplined saving habits with transparent tools and choices you control."),
  linkedInVariant("v5", "p2", "Good financial habits are rarely about one dramatic move. They are about clear choices you can repeat and review.", "Progress you can understand"),
  emailVariant("v6", "p2", "Keep your plan on your terms", "Hi Arjun,\n\nYour next step should come with context, not pressure. Review your options, choose a pace, and see how each habit supports the goals you set."),
  googleVariant("v7", "p3", "Saving that flexes with work", "Create a flexible personal routine that can adapt when business income changes."),
  linkedInVariant("v8", "p3", "Business months change. Your personal progress does not have to stop every time they do.", "A money routine built to flex"),
  emailVariant("v9", "p3", "A plan for uneven months", "Hi Leena,\n\nNestWise makes it easier to keep personal goals visible while business takes the spotlight. Set a flexible rhythm now, then adjust it whenever the month changes."),
];

export const findings: PolicyFinding[] = [
  {
    id: "f1",
    variantId: "v1",
    source: "deterministic",
    ruleId: "FIN-BANNED-001",
    severity: "blocking",
    findingType: "Prohibited certainty claim",
    evidence: "“guaranteed returns”",
    message: "Investment messaging must not imply that returns are guaranteed.",
    suggestion: "Describe the habit or product experience without promising an outcome.",
    resolved: true,
  },
  {
    id: "f2",
    variantId: "v1",
    source: "deterministic",
    ruleId: "FIN-DISC-002",
    severity: "high",
    findingType: "Missing risk disclosure",
    evidence: "Original Google Search draft had no disclosure.",
    message: "Investing creative should include a visible risk statement.",
    suggestion: "Add: Investing involves risk. Returns are not guaranteed.",
    resolved: true,
  },
  {
    id: "f3",
    variantId: "v8",
    source: "semantic_ai",
    severity: "low",
    findingType: "Persona tone",
    evidence: "“does not have to stop”",
    message: "The phrasing may feel slightly absolute for an audience with variable income.",
    suggestion: "Keep the flexibility benefit, but acknowledge that plans may pause.",
    resolved: false,
  },
  {
    id: "f4",
    variantId: "v5",
    source: "semantic_ai",
    severity: "info",
    findingType: "Cross-channel consistency",
    evidence: "“Progress you can understand”",
    message: "Strong alignment with the transparent-choice message used across this journey.",
    resolved: false,
  },
];

const scores = [92, 88, 90, 86, 91, 84, 78, 73, 80];
export const evaluationScores: EvaluationScore[] = variants.map((variant, index) => ({
  variantId: variant.id,
  personaId: variant.personaId,
  channel: variant.channel,
  messageFit: Math.min(96, scores[index] + (index % 3 === 0 ? 2 : 0)),
  channelFit: Math.min(95, scores[index] + 1),
  ctaClarity: index % 3 === 2 ? 91 : 86,
  policyQuality: variant.id === "v1" ? 88 : 96,
  journeyConsistency: Math.min(94, scores[index] + 3),
  weightedTotal: scores[index],
  rationale: scores[index] >= 88 ? "Strong persona fit and clear next action." : scores[index] >= 80 ? "Solid foundation with room to sharpen the message angle." : "Relevant premise, but the promise needs a more specific and flexible framing.",
}));

export const allocationChanges: AllocationChange[] = journeySteps.map((step, index) => {
  const wave2 = [17, 13, 9, 14, 13, 9, 9, 8, 8][index];
  return {
    personaId: step.personaId,
    channel: step.channel,
    wave1: step.allocationPercent,
    wave2,
    reasonCode:
      wave2 > step.allocationPercent ? "Increase: high readiness" : wave2 < step.allocationPercent ? "Reduce and refine" : "Maintain",
  };
});

export const completedStages: WorkflowStage[] = [
  { id: "brief", label: "Brief", eyebrow: "Input", status: "completed", summary: "1 structured campaign brief" },
  { id: "strategy", label: "Strategy", eyebrow: "AI assist", status: "completed", summary: "3 personas · 3 KPIs" },
  { id: "journey", label: "Journey", eyebrow: "Plan", status: "completed", summary: "9 connected steps" },
  { id: "creative", label: "Creative", eyebrow: "Generate", status: "completed", summary: "9 channel variants" },
  { id: "policy", label: "Policy", eyebrow: "Deterministic", status: "warning", summary: "2 findings resolved" },
  { id: "semantic", label: "Semantic review", eyebrow: "AI assist", status: "completed", summary: "1 advisory note" },
  { id: "approval", label: "Approval", eyebrow: "Human gate", status: "approval_required", summary: "Ready for your decision" },
  { id: "deploy", label: "Mock deploy", eyebrow: "Preview", status: "pending", summary: "Platform-shaped payloads" },
  { id: "evaluation", label: "Evaluation", eyebrow: "Synthetic", status: "pending", summary: "Directional scoring" },
  { id: "wave2", label: "Wave 2", eyebrow: "Adapt", status: "pending", summary: "Allocation proposal" },
];

export const channelLabels: Record<string, string> = {
  google_search: "Google Search",
  linkedin_sponsored_post: "LinkedIn",
  email: "Email",
};
