import { useMemo } from "react";
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Check,
  ChevronRight,
  CircleGauge,
  Info,
  Lightbulb,
  LockKeyhole,
  Minus,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  WandSparkles,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  allocationChanges as demoAllocationChanges,
  channelLabels,
  evaluationScores as demoEvaluationScores,
  personas as demoPersonas,
  variants as demoVariants,
} from "../../data/demo";
import type { AdaptedWave2 } from "../../api/adapt";
import type { AllocationChange, CampaignStatus, CreativeVariant, EvaluationScore, Persona } from "../../types";

interface ResultsTabProps {
  status: CampaignStatus;
  onReviewCreative: () => void;
  personas?: Persona[];
  variants?: CreativeVariant[];
  evaluationScores?: EvaluationScore[];
  allocationChanges?: AllocationChange[];
  wave2?: AdaptedWave2;
}

const FACTOR_DIMENSIONS: { key: keyof EvaluationScore & string; name: string }[] = [
  { key: "messageFit", name: "Message fit" },
  { key: "channelFit", name: "Channel fit" },
  { key: "ctaClarity", name: "CTA clarity" },
  { key: "policyQuality", name: "Policy quality" },
  { key: "journeyConsistency", name: "Journey consistency" },
];

function leadLine(copy: Record<string, unknown>): string {
  if (Array.isArray(copy.descriptions)) return (copy.descriptions as string[])[0] ?? "";
  if (typeof copy.introText === "string") return copy.introText;
  if (typeof copy.intro_text === "string") return copy.intro_text as string;
  if (typeof copy.subject === "string") return copy.subject;
  return "";
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number; name: string; color: string }[]; label?: string }) => active && payload?.length ? <div className="chart-tooltip"><strong>{label}</strong>{payload.map((item) => <span key={item.name}><i style={{ background: item.color }} />{item.name}: {item.value}{item.value <= 50 ? "%" : ""}</span>)}</div> : null;

export function ResultsTab({
  status,
  onReviewCreative,
  personas: personasProp,
  variants: variantsProp,
  evaluationScores: evaluationScoresProp,
  allocationChanges: allocationChangesProp,
  wave2,
}: ResultsTabProps) {
  const personas = personasProp?.length ? personasProp : demoPersonas;
  const variants = variantsProp?.length ? variantsProp : demoVariants;
  const evaluationScores = evaluationScoresProp?.length ? evaluationScoresProp : demoEvaluationScores;
  const allocationChanges = allocationChangesProp?.length ? allocationChangesProp : demoAllocationChanges;

  const complete = status === "completed";
  const overall = Math.round(evaluationScores.reduce((sum, item) => sum + item.weightedTotal, 0) / evaluationScores.length);

  const factorData = useMemo(
    () =>
      FACTOR_DIMENSIONS.map(({ key, name }) => ({
        name,
        score: Math.round(evaluationScores.reduce((sum, item) => sum + (item[key] as number), 0) / evaluationScores.length),
      })),
    [evaluationScores],
  );

  const allocationData = useMemo(
    () =>
      personas.map((persona) => ({
        name: persona.shortName,
        wave1: allocationChanges.filter((item) => item.personaId === persona.id).reduce((sum, item) => sum + item.wave1, 0),
        wave2: allocationChanges.filter((item) => item.personaId === persona.id).reduce((sum, item) => sum + item.wave2, 0),
      })),
    [personas, allocationChanges],
  );

  const topVariant = useMemo(
    () => evaluationScores.reduce<EvaluationScore | undefined>((best, item) => (!best || item.weightedTotal > best.weightedTotal ? item : best), undefined),
    [evaluationScores],
  );
  const weakestVariant = useMemo(
    () => evaluationScores.reduce<EvaluationScore | undefined>((worst, item) => (!worst || item.weightedTotal < worst.weightedTotal ? item : worst), undefined),
    [evaluationScores],
  );
  const weakestPersonaName = weakestVariant ? personas.find((item) => item.id === weakestVariant.personaId)?.shortName : undefined;
  const readyVariants = variants.filter((item) => item.status === "policy_ready").length;
  const blockedVariants = variants.filter((item) => item.status === "blocked").length;
  const avgShift = allocationChanges.length
    ? Math.round(allocationChanges.reduce((sum, item) => sum + Math.abs(item.wave2 - item.wave1), 0) / allocationChanges.length)
    : 0;

  const rewrite = wave2?.rewrites[0];
  const rewriteVariant = rewrite ? variants.find((item) => item.id === rewrite.client_variant_id.replace(/_r\d+$/, "")) : undefined;
  const rewritePersona = (rewriteVariant && personas.find((item) => item.id === rewriteVariant.personaId)) || personas[2];
  const rewriteEval = rewriteVariant ? evaluationScores.find((item) => item.variantId === rewriteVariant.id) : undefined;
  const rewriteLabel = rewriteVariant ? `${rewritePersona.shortName} · ${channelLabels[rewriteVariant.channel]}` : "Leena · LinkedIn";
  const rewriteStageScore = rewriteVariant
    ? `${rewriteVariant.journeyStage} · Score ${rewriteEval ? Math.round(rewriteEval.weightedTotal) : "—"}`
    : "Consideration · Score 73";
  const rewriteBefore = rewriteVariant
    ? leadLine(rewriteVariant.copy as unknown as Record<string, unknown>)
    : "Business months change. Your personal progress does not have to stop every time they do.";
  const rewriteAfter = rewrite
    ? leadLine(rewrite.rewritten_copy)
    : "When business months change, a flexible personal plan gives you a clear place to pause, adjust, and begin again.";

  const rationale = wave2?.rationale;
  const rationaleHeading = rationale ? "Wave 2 allocation rationale" : "Change the framing, not the promise";
  const rationaleBody =
    rationale?.rationale ??
    "Leena responded to flexibility, but the original line sounded too absolute. Wave 2 keeps the practical benefit while acknowledging that progress may pause during uneven business months.";
  const rationaleTags = rationale?.allocation_summary.slice(0, 3) ?? ["Persona sensitivity", "Policy quality", "Journey consistency"];

  return (
    <div className={`page page-results ${!complete ? "results-preview" : ""}`}>
      <section className="page-heading heading-with-action">
        <div><div className="breadcrumb"><span>Campaigns</span><ChevronRight size={13} />NestWise · Summer acquisition<ChevronRight size={13} />Results</div><h1>Directional readiness, explained</h1><p>Transparent synthetic scoring turns the approved campaign into a measurable Wave 2 recommendation.</p></div>
        <div className="results-heading-actions"><span className="method-badge"><CircleGauge size={15} /> Synthetic pre-flight v1.0</span><button type="button" className="secondary-button" onClick={onReviewCreative}>Review creative</button></div>
      </section>

      {!complete && <div className="results-lock-banner"><LockKeyhole size={18} /><div><strong>Cached result preview</strong><p>Approve the creative to run mock deployment, evaluation, and Wave 2 in sequence.</p></div><button type="button" onClick={onReviewCreative}>Go to approval <ArrowRight size={14} /></button></div>}

      <section className="readiness-hero panel">
        <div className="score-hero">
          <div className="large-score-ring" style={{ "--score": overall } as React.CSSProperties}><div><strong>{overall}</strong><span>/ 100</span></div></div>
          <div><span className="eyebrow">Overall readiness</span><h2>Strong foundation for Wave 2</h2><p>Creative is policy-ready and matched to each persona's journey.{weakestPersonaName ? ` ${weakestPersonaName}'s journey has the clearest opportunity for refinement.` : ""}</p><div className="confidence-row"><span><Check />{blockedVariants} open blockers</span><span><TrendingUp />{factorData.filter((item) => item.score > 85).length} of {factorData.length} factors above 85</span></div></div>
        </div>
        <div className="hero-divider" />
        <div className="score-summary-grid">
          <div><span>Top variant</span><strong>{topVariant ? Math.round(topVariant.weightedTotal) : "—"}</strong><p>{topVariant ? `${personas.find((item) => item.id === topVariant.personaId)?.shortName ?? ""} · ${channelLabels[topVariant.channel]}` : "—"}</p></div>
          <div><span>Needs attention</span><strong>{weakestVariant ? Math.round(weakestVariant.weightedTotal) : "—"}</strong><p>{weakestVariant ? `${personas.find((item) => item.id === weakestVariant.personaId)?.shortName ?? ""} · ${channelLabels[weakestVariant.channel]}` : "—"}</p></div>
          <div><span>Ready variants</span><strong>{readyVariants}/{variants.length}</strong><p>No deterministic blockers</p></div>
          <div><span>Wave 2 shift</span><strong>{avgShift} pts</strong><p>Reallocated directionally</p></div>
        </div>
      </section>

      <div className="results-grid">
        <section className="panel chart-panel factor-panel">
          <div className="panel-topline"><div><span className="eyebrow">Factor breakdown</span><h2>Why the campaign scored {overall}</h2></div><span className="directional-label"><Info size={12} /> Directional</span></div>
          <div className="factor-chart">
            <ResponsiveContainer width="100%" height="100%"><BarChart layout="vertical" data={factorData} margin={{ top: 4, right: 36, bottom: 0, left: 8 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e1da" /><XAxis type="number" domain={[0, 100]} tick={{ fill: "#888980", fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis type="category" dataKey="name" width={112} tick={{ fill: "#393d3a", fontSize: 12 }} axisLine={false} tickLine={false} /><Tooltip content={<CustomTooltip />} cursor={{ fill: "#f5f4ef" }} /><Bar dataKey="score" radius={[0, 5, 5, 0]} barSize={19}>{factorData.map((entry) => <Cell key={entry.name} fill={entry.score >= 92 ? "#2f7d67" : entry.score >= 87 ? "#526f64" : "#e56848"} />)}<LabelList dataKey="score" position="right" fill="#2a2e2b" fontSize={12} fontWeight={700} /></Bar></BarChart></ResponsiveContainer>
          </div>
          <div className="score-method"><ShieldCheck size={16} /><p><strong>Transparent rubric:</strong> Message fit 30% · Channel fit 20% · CTA clarity 15% · Policy quality 20% · Journey consistency 15%</p></div>
        </section>

        <section className="panel chart-panel allocation-panel">
          <div className="panel-topline"><div><span className="eyebrow">Allocation proposal</span><h2>Wave 1 → Wave 2</h2></div><div className="chart-legend"><span><i className="wave1" />Wave 1</span><span><i className="wave2" />Wave 2</span></div></div>
          <div className="allocation-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={allocationData} margin={{ top: 12, right: 0, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e1da" /><XAxis dataKey="name" tick={{ fill: "#50534f", fontSize: 12 }} axisLine={false} tickLine={false} /><YAxis domain={[0, 45]} tick={{ fill: "#888980", fontSize: 11 }} axisLine={false} tickLine={false} /><Tooltip content={<CustomTooltip />} cursor={{ fill: "#f5f4ef" }} /><Bar dataKey="wave1" name="Wave 1" fill="#c8c7be" radius={[4, 4, 0, 0]} barSize={23} /><Bar dataKey="wave2" name="Wave 2" fill="#2f7d67" radius={[4, 4, 0, 0]} barSize={23} /></BarChart></ResponsiveContainer></div>
          <div className="allocation-insight"><TrendingUp size={17} /><div><strong>Shift toward proven intent</strong><p>Increase allocation where readiness is strongest; preserve a smaller learning budget where messages are still being refined.</p></div></div>
        </section>
      </div>

      <section className="panel allocation-table-panel">
        <div className="panel-topline"><div><span className="eyebrow">Decision trail</span><h2>Every allocation change, with a reason</h2></div><span className="count-badge">Normalized to 100%</span></div>
        <div className="allocation-table-wrap"><table className="allocation-table"><thead><tr><th>Persona</th><th>Channel</th><th>Wave 1</th><th>Wave 2</th><th>Change</th><th>Reason</th></tr></thead><tbody>{allocationChanges.map((change) => {
          const persona = personas.find((item) => item.id === change.personaId) ?? personas[0];
          const delta = change.wave2 - change.wave1;
          return <tr key={`${change.personaId}-${change.channel}`}><td><span className="mini-persona" style={{ background: persona.accent }}>{persona.shortName[0]}</span><strong>{persona.shortName}</strong></td><td>{channelLabels[change.channel]}</td><td>{change.wave1}%</td><td><strong>{change.wave2}%</strong></td><td><span className={`delta ${delta > 0 ? "up" : delta < 0 ? "down" : "same"}`}>{delta > 0 ? <ArrowUpRight size={13} /> : delta < 0 ? <ArrowDownRight size={13} /> : <Minus size={13} />}{delta > 0 ? "+" : ""}{delta} pts</span></td><td>{change.reasonCode}</td></tr>;
        })}</tbody></table></div>
      </section>

      <div className="wave2-grid">
        <section className="panel rewrite-panel">
          <div className="panel-topline"><div><span className="eyebrow">Wave 2 creative</span><h2>One targeted rewrite</h2></div><span className="ai-label"><WandSparkles size={13} /> AI-assisted</span></div>
          <div className="rewrite-context"><span className="mini-persona" style={{ background: rewritePersona.accent }}>{rewriteLabel[0]}</span><div><strong>{rewriteLabel}</strong><p>{rewriteStageScore}</p></div></div>
          <div className="rewrite-comparison">
            <div><span>Wave 1</span><p>“{rewriteBefore}”</p></div>
            <div className="rewrite-arrow"><ArrowRight size={16} /></div>
            <div className="new-copy"><span>Wave 2</span><p>“{rewriteAfter}”</p></div>
          </div>
        </section>
        <section className="panel rationale-panel">
          <div className="rationale-icon"><Lightbulb size={19} /></div><span className="eyebrow">Optimizer rationale</span><h2>{rationaleHeading}</h2><p>{rationaleBody}</p>
          <div className="rationale-tags">{rationaleTags.map((tag) => <span key={tag}><Check size={12} />{tag}</span>)}</div>
        </section>
      </div>

      <footer className="results-footnote"><BarChart3 size={16} /><p><strong>About these results:</strong> This is a transparent synthetic pre-flight evaluation, not attribution or a prediction of conversions, CPA, or ROAS. Production measurement would replace this rubric with live telemetry.</p></footer>
    </div>
  );
}
