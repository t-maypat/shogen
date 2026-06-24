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
import { allocationChanges, channelLabels, evaluationScores, personas, variants } from "../../data/demo";
import type { CampaignStatus } from "../../types";

interface ResultsTabProps {
  status: CampaignStatus;
  onReviewCreative: () => void;
}

const factorData = [
  { name: "Message fit", score: 86 },
  { name: "Channel fit", score: 87 },
  { name: "CTA clarity", score: 88 },
  { name: "Policy quality", score: 95 },
  { name: "Journey consistency", score: 88 },
];

const allocationData = personas.map((persona) => ({
  name: persona.shortName,
  wave1: allocationChanges.filter((item) => item.personaId === persona.id).reduce((sum, item) => sum + item.wave1, 0),
  wave2: allocationChanges.filter((item) => item.personaId === persona.id).reduce((sum, item) => sum + item.wave2, 0),
}));

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number; name: string; color: string }[]; label?: string }) => active && payload?.length ? <div className="chart-tooltip"><strong>{label}</strong>{payload.map((item) => <span key={item.name}><i style={{ background: item.color }} />{item.name}: {item.value}{item.value <= 50 ? "%" : ""}</span>)}</div> : null;

export function ResultsTab({ status, onReviewCreative }: ResultsTabProps) {
  const complete = status === "completed";
  const overall = Math.round(evaluationScores.reduce((sum, item) => sum + item.weightedTotal, 0) / evaluationScores.length);

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
          <div><span className="eyebrow">Overall readiness</span><h2>Strong foundation for Wave 2</h2><p>Creative is policy-ready and well matched to the first two personas. Leena’s journey has the clearest opportunity for refinement.</p><div className="confidence-row"><span><Check />0 open blockers</span><span><TrendingUp />4 of 5 factors above 85</span></div></div>
        </div>
        <div className="hero-divider" />
        <div className="score-summary-grid">
          <div><span>Top variant</span><strong>92</strong><p>Maya · Google Search</p></div>
          <div><span>Needs attention</span><strong>73</strong><p>Leena · LinkedIn</p></div>
          <div><span>Ready variants</span><strong>9/9</strong><p>No deterministic blockers</p></div>
          <div><span>Wave 2 shift</span><strong>8 pts</strong><p>Reallocated directionally</p></div>
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
          <div className="allocation-insight"><TrendingUp size={17} /><div><strong>Shift toward proven intent</strong><p>Increase Maya and Arjun where readiness is strongest; preserve a smaller learning budget for Leena’s revised message.</p></div></div>
        </section>
      </div>

      <section className="panel allocation-table-panel">
        <div className="panel-topline"><div><span className="eyebrow">Decision trail</span><h2>Every allocation change, with a reason</h2></div><span className="count-badge">Normalized to 100%</span></div>
        <div className="allocation-table-wrap"><table className="allocation-table"><thead><tr><th>Persona</th><th>Channel</th><th>Wave 1</th><th>Wave 2</th><th>Change</th><th>Reason</th></tr></thead><tbody>{allocationChanges.map((change) => {
          const persona = personas.find((item) => item.id === change.personaId)!;
          const delta = change.wave2 - change.wave1;
          return <tr key={`${change.personaId}-${change.channel}`}><td><span className="mini-persona" style={{ background: persona.accent }}>{persona.shortName[0]}</span><strong>{persona.shortName}</strong></td><td>{channelLabels[change.channel]}</td><td>{change.wave1}%</td><td><strong>{change.wave2}%</strong></td><td><span className={`delta ${delta > 0 ? "up" : delta < 0 ? "down" : "same"}`}>{delta > 0 ? <ArrowUpRight size={13} /> : delta < 0 ? <ArrowDownRight size={13} /> : <Minus size={13} />}{delta > 0 ? "+" : ""}{delta} pts</span></td><td>{change.reasonCode}</td></tr>;
        })}</tbody></table></div>
      </section>

      <div className="wave2-grid">
        <section className="panel rewrite-panel">
          <div className="panel-topline"><div><span className="eyebrow">Wave 2 creative</span><h2>One targeted rewrite</h2></div><span className="ai-label"><WandSparkles size={13} /> AI-assisted</span></div>
          <div className="rewrite-context"><span className="mini-persona" style={{ background: personas[2].accent }}>L</span><div><strong>Leena · LinkedIn</strong><p>Consideration · Score 73</p></div><span className="delta down"><ArrowDownRight size={13} /> 1 pt</span></div>
          <div className="rewrite-comparison">
            <div><span>Wave 1</span><p>“Business months change. Your personal progress does not have to stop every time they do.”</p></div>
            <div className="rewrite-arrow"><ArrowRight size={16} /></div>
            <div className="new-copy"><span>Wave 2</span><p>“When business months change, a flexible personal plan gives you a clear place to pause, adjust, and begin again.”</p></div>
          </div>
        </section>
        <section className="panel rationale-panel">
          <div className="rationale-icon"><Lightbulb size={19} /></div><span className="eyebrow">Optimizer rationale</span><h2>Change the framing, not the promise</h2><p>Leena responded to flexibility, but the original line sounded too absolute. Wave 2 keeps the practical benefit while acknowledging that progress may pause during uneven business months.</p>
          <div className="rationale-tags"><span><Check size={12} /> Persona sensitivity</span><span><Check size={12} /> Policy quality</span><span><Check size={12} /> Journey consistency</span></div>
        </section>
      </div>

      <footer className="results-footnote"><BarChart3 size={16} /><p><strong>About these results:</strong> This is a transparent synthetic pre-flight evaluation, not attribution or a prediction of conversions, CPA, or ROAS. Production measurement would replace this rubric with live telemetry.</p></footer>
    </div>
  );
}
