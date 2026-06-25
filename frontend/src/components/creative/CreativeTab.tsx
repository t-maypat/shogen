import { useMemo, useState } from "react";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Clock3,
  ExternalLink,
  History,
  Info,
  Mail,
  Megaphone,
  Search,
  ShieldCheck,
  Sparkles,
  WandSparkles,
} from "lucide-react";
import {
  channelLabels,
  findings as demoFindings,
  personas as demoPersonas,
  variants as demoVariants,
} from "../../data/demo";
import type { CampaignStatus, Channel, CreativeVariant, Persona, PolicyFinding } from "../../types";

interface CreativeTabProps {
  status: CampaignStatus;
  onApprove: () => void;
  approving?: boolean;
  variants?: CreativeVariant[];
  findings?: PolicyFinding[];
  personas?: Persona[];
}

const channels: { id: Channel; label: string; icon: typeof Search }[] = [
  { id: "google_search", label: "Google Search", icon: Search },
  { id: "linkedin_sponsored_post", label: "LinkedIn", icon: Megaphone },
  { id: "email", label: "Email", icon: Mail },
];

function GooglePreview({ variant }: { variant: CreativeVariant }) {
  if (variant.copy.type !== "google") return null;
  return <div className="ad-preview google-preview">
    <div className="google-top"><span className="nestwise-favicon">N</span><div><strong>Sponsored</strong><span>nestwise.app › {variant.copy.path.split("/").at(-1)}</span></div><span className="ad-more">⋮</span></div>
    <h3>{variant.copy.headlines[0]} | {variant.copy.headlines[1]}</h3>
    <p>{variant.copy.descriptions[0]} {variant.copy.descriptions[1]}</p>
    <div className="google-sitelinks"><span>How NestWise works</span><span>Build a saving plan</span></div>
  </div>;
}

function LinkedInPreview({ variant }: { variant: CreativeVariant }) {
  if (variant.copy.type !== "linkedin") return null;
  return <div className="ad-preview linkedin-preview">
    <div className="linkedin-brand"><span className="nestwise-logo">N</span><div><strong>NestWise</strong><span>12,841 followers</span><span>Promoted · <span aria-hidden>◉</span></span></div><span className="ad-more">•••</span></div>
    <p className="linkedin-intro">{variant.copy.introText}</p>
    <div className="linkedin-art"><div className="art-orbit one" /><div className="art-orbit two" /><span>Build at<br /><em>your pace.</em></span><div className="art-card"><i>NW</i><strong>One clear habit</strong><small>Week by week</small></div></div>
    <div className="linkedin-link"><div><span>nestwise.app</span><strong>{variant.copy.headline}</strong><p>{variant.copy.description}</p></div><button>{variant.copy.cta}</button></div>
    <div className="linkedin-reactions"><span>◉ ♡ △ 184</span><span>12 comments · 7 reposts</span></div>
  </div>;
}

function EmailPreview({ variant }: { variant: CreativeVariant }) {
  if (variant.copy.type !== "email") return null;
  return <div className="email-client">
    <div className="email-toolbar"><span>‹</span><span>Archive</span><span>Report</span><span>Delete</span><span className="email-toolbar-more">•••</span></div>
    <div className="email-meta"><span className="nestwise-logo">N</span><div><strong>NestWise team</strong><span>to me⌄</span></div><time>10:24 AM</time></div>
    <div className="email-subject"><strong>{variant.copy.subject}</strong><span>{variant.copy.preheader}</span></div>
    <div className="email-body"><div className="email-brand">NESTWISE</div>{variant.copy.body.split("\n").map((line, index) => <p key={index}>{line || <br />}</p>)}<button>{variant.copy.cta}</button><small>{variant.disclosure}</small></div>
  </div>;
}

export function CreativeTab({
  status,
  onApprove,
  approving = false,
  variants: variantsProp,
  findings: findingsProp,
  personas: personasProp,
}: CreativeTabProps) {
  const variants = variantsProp?.length ? variantsProp : demoVariants;
  const findings = findingsProp?.length ? findingsProp : demoFindings;
  const personas = personasProp?.length ? personasProp : demoPersonas;
  const [personaId, setPersonaId] = useState("p1");
  const [channel, setChannel] = useState<Channel>("google_search");
  const [reviewTab, setReviewTab] = useState<"findings" | "history">("findings");
  const variant = variants.find((item) => item.personaId === personaId && item.channel === channel) ?? variants[0];
  const selectedFindings = findings.filter((finding) => finding.variantId === variant.id);
  const persona = personas.find((item) => item.id === personaId) ?? personas[0];
  const ready = status === "approval_required" && !approving;
  const complete = status === "completed" || status === "approved" || status === "evaluating";

  const summary = useMemo(() => ({
    ready: variants.filter((item) => item.status === "policy_ready").length,
    warning: variants.filter((item) => item.status === "warning").length,
    blocking: findings.filter((item) => item.severity === "blocking" && !item.resolved).length,
  }), [variants, findings]);

  return (
    <div className="page page-creative">
      <section className="page-heading heading-with-action creative-heading">
        <div><div className="breadcrumb"><span>Campaigns</span><ChevronRight size={13} />NestWise · Summer acquisition<ChevronRight size={13} />Creative review</div><h1>Review the creative system</h1><p>Inspect each persona-channel decision, its policy trail, and the revision that produced the current draft.</p></div>
        <div className="review-summary"><div><strong>{summary.ready}</strong><span>Policy-ready</span></div><div><strong>{summary.warning}</strong><span>Advisory note</span></div><div><strong>{summary.blocking}</strong><span>Open blockers</span></div></div>
      </section>

      <div className="creative-toolbar panel">
        <div className="selector-group persona-selector"><span>Persona</span><div>{personas.map((item) => <button type="button" key={item.id} className={item.id === personaId ? "active" : ""} onClick={() => setPersonaId(item.id)}><i style={{ background: item.accent }}>{item.shortName[0]}</i><span>{item.shortName}</span><small>{item.riskSensitivity} sensitivity</small></button>)}</div></div>
        <div className="toolbar-divider" />
        <div className="selector-group channel-selector"><span>Channel</span><div>{channels.map(({ id, label, icon: Icon }) => <button type="button" key={id} className={id === channel ? "active" : ""} onClick={() => setChannel(id)}><Icon size={15} />{label}<em>{variants.find((item) => item.personaId === personaId && item.channel === id)?.status === "warning" ? "!" : <Check size={11} />}</em></button>)}</div></div>
      </div>

      <div className="creative-layout">
        <section className="panel preview-panel">
          <div className="preview-panel-header">
            <div><span className="eyebrow">Channel preview</span><h2>{channelLabels[channel]}</h2></div>
            <div className="preview-meta"><span className="stage-chip">{variant.journeyStage}</span><span className={`creative-status ${variant.status}`}><ShieldCheck size={13} />{variant.status.replace("_", " ")}</span><button className="icon-button" aria-label="Open preview"><ExternalLink size={15} /></button></div>
          </div>
          <div className={`preview-stage preview-${channel}`}>
            {variant.copy.type === "google" && <GooglePreview variant={variant} />}
            {variant.copy.type === "linkedin" && <LinkedInPreview variant={variant} />}
            {variant.copy.type === "email" && <EmailPreview variant={variant} />}
          </div>
          <div className="preview-caption"><span>Preview only</span><p>Platform-shaped rendering for review. Not a deployable or platform-certified payload.</p><span>Variant {variant.id.toUpperCase()} · rev {variant.revision}</span></div>
        </section>

        <aside className="panel review-panel">
          <div className="review-panel-tabs"><button type="button" onClick={() => setReviewTab("findings")} className={reviewTab === "findings" ? "active" : ""}><ShieldCheck size={15} /> Review</button><button type="button" onClick={() => setReviewTab("history")} className={reviewTab === "history" ? "active" : ""}><History size={15} /> Revision trail</button></div>
          {reviewTab === "findings" ? <div className="findings-content">
            <div className="review-score"><div className="score-ring"><strong>{variant.status === "warning" ? 87 : 96}</strong><span>/100</span></div><div><span className="eyebrow">Policy quality</span><h3>{variant.status === "warning" ? "Ready with note" : "Ready for approval"}</h3><p>Deterministic checks passed on the current revision.</p></div></div>
            <div className="findings-section-title"><span>Deterministic checks</span><small>{selectedFindings.filter((item) => item.source === "deterministic").length || "All"} reviewed</small></div>
            {selectedFindings.filter((item) => item.source === "deterministic").length ? selectedFindings.filter((item) => item.source === "deterministic").map((finding) => <div className={`finding-card ${finding.resolved ? "resolved" : "open"}`} key={finding.id}><div className="finding-title"><span>{finding.resolved ? <CheckCircle2 size={15} /> : <CircleAlert size={15} />}{finding.findingType}</span><em>{finding.resolved ? "Resolved" : finding.severity}</em></div><div className="finding-evidence">{finding.evidence}</div><p>{finding.message}</p>{finding.suggestion && <small><WandSparkles size={12} />{finding.suggestion}</small>}</div>) : <div className="empty-review"><CheckCircle2 size={17} /><span>All 12 deterministic checks passed</span></div>}
            <div className="findings-section-title"><span>Semantic AI review</span><small>Advisory only</small></div>
            {selectedFindings.filter((item) => item.source === "semantic_ai").length ? selectedFindings.filter((item) => item.source === "semantic_ai").map((finding) => <div className="finding-card semantic" key={finding.id}><div className="finding-title"><span><Sparkles size={15} />{finding.findingType}</span><em>{finding.severity}</em></div><div className="finding-evidence">{finding.evidence}</div><p>{finding.message}</p><small><WandSparkles size={12} />{finding.suggestion}</small></div>) : <div className="empty-review"><CheckCircle2 size={17} /><span>Tone, sensitivity, and consistency passed</span></div>}
            <div className="disclosure-block"><Info size={14} /><div><span>Disclosure on current variant</span><p>{variant.disclosure}</p></div></div>
          </div> : <div className="history-content">
            <div className="timeline-label"><span>Current</span><i /></div>
            <div className="history-version current"><div><strong>Revision {variant.revision}</strong><span>Policy-ready</span></div><p>{variant.copy.type === "google" ? variant.copy.descriptions[0] : variant.copy.type === "linkedin" ? variant.copy.introText : variant.copy.subject}</p><small><Check size={12} /> Passed deterministic review</small></div>
            {variant.previousCopy ? <><div className="revision-connector"><WandSparkles size={14} />Rewritten by Shogun from 2 findings</div><div className="history-version previous"><div><strong>Original draft</strong><span>Blocked</span></div><p>{variant.previousCopy}</p><small><CircleAlert size={12} /> “guaranteed returns” · missing disclosure</small></div></> : <div className="history-empty"><History size={20} /><h3>No rewrite needed</h3><p>This variant passed on its original generation.</p></div>}
            <div className="history-principle"><strong>Originals stay visible.</strong><p>Shogun preserves every revision so a marketer can see what changed and why.</p></div>
          </div>}
        </aside>
      </div>

      <section className={`approval-bar ${complete ? "approved" : ""}`}>
        <div className="approval-icon">{complete ? <CheckCircle2 size={21} /> : <ShieldCheck size={21} />}</div>
        <div><span className="eyebrow">Human approval gate</span><h3>{complete ? "Campaign approved" : ready ? "All blocking findings are resolved" : "Review is still in progress"}</h3><p>{complete ? "Mock deployment and synthetic evaluation have been authorized." : "One non-blocking semantic note remains. Final legal and platform review stays with your team."}</p></div>
        <div className="approval-evidence"><span><Check size={13} /> {variants.length} variants reviewed</span><span><Check size={13} /> {summary.blocking} open blockers</span></div>
        <button type="button" className="primary-button approve-button" onClick={onApprove} disabled={!ready}>{complete ? <><Check size={16} /> Approved</> : approving ? <><span className="button-spinner" /> Approving</> : <><ShieldCheck size={16} /> Approve for mock deployment <ArrowRight size={15} /></>}</button>
      </section>
    </div>
  );
}
