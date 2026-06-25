import { useMemo, useState } from "react";
import {
  Background,
  BackgroundVariant,
  Edge,
  MarkerType,
  Node,
  ReactFlow,
} from "@xyflow/react";
import {
  ArrowRight,
  Check,
  ChevronRight,
  CircleAlert,
  Clock3,
  Mail,
  Megaphone,
  Search,
  ShieldAlert,
  Sparkles,
  Target,
  UserRound,
  Users,
  WandSparkles,
} from "lucide-react";
import {
  channelLabels,
  journeySteps as demoJourneySteps,
  kpis as demoKpis,
  personas as demoPersonas,
} from "../../data/demo";
import type { CampaignStatus, JourneyStep, KPI, Persona, WorkflowStage } from "../../types";

interface JourneyTabProps {
  stages: WorkflowStage[];
  status: CampaignStatus;
  onOpenCreative: () => void;
  personas?: Persona[];
  kpis?: KPI[];
  journeySteps?: JourneyStep[];
}

const stageIcons = [Target, Users, ArrowRight, WandSparkles, ShieldAlert, Sparkles, UserRound, ArrowRight, Target, Sparkles];
const positions = [
  { x: 20, y: 50 }, { x: 240, y: 50 }, { x: 460, y: 50 }, { x: 680, y: 50 }, { x: 900, y: 50 },
  { x: 900, y: 240 }, { x: 680, y: 240 }, { x: 460, y: 240 }, { x: 240, y: 240 }, { x: 20, y: 240 },
];

function StageNodeLabel({ stage, index }: { stage: WorkflowStage; index: number }) {
  const Icon = stageIcons[index];
  return (
    <div className="flow-node-content">
      <div className={`flow-node-icon ${stage.status}`}>
        {stage.status === "completed" ? <Check size={14} /> : stage.status === "running" ? <Sparkles size={14} /> : stage.status === "warning" ? <CircleAlert size={14} /> : <Icon size={14} />}
      </div>
      <div><span>{stage.eyebrow}</span><strong>{stage.label}</strong><small>{stage.summary}</small></div>
    </div>
  );
}

export function JourneyTab({
  stages,
  status,
  onOpenCreative,
  personas = demoPersonas,
  kpis = demoKpis,
  journeySteps = demoJourneySteps,
}: JourneyTabProps) {
  const [selectedStageId, setSelectedStageId] = useState("approval");
  const [selectedPersona, setSelectedPersona] = useState("p1");
  const selectedStage = stages.find((stage) => stage.id === selectedStageId) ?? stages[0];

  const nodes: Node[] = useMemo(() => stages.map((stage, index) => ({
    id: stage.id,
    position: positions[index],
    data: { label: <StageNodeLabel stage={stage} index={index} /> },
    className: `workflow-node workflow-node-${stage.status} ${selectedStageId === stage.id ? "selected" : ""}`,
    style: { width: 184, height: 96 },
    draggable: false,
    selectable: true,
  })), [stages, selectedStageId]);

  const edges: Edge[] = useMemo(() => stages.slice(0, -1).map((stage, index) => ({
    id: `${stage.id}-${stages[index + 1].id}`,
    source: stage.id,
    target: stages[index + 1].id,
    type: "smoothstep",
    animated: stages[index + 1].status === "running",
    markerEnd: { type: MarkerType.ArrowClosed, color: stages[index + 1].status === "pending" ? "#b8b8ae" : "#496f61" },
    style: { stroke: stages[index + 1].status === "pending" ? "#c8c7be" : "#6a8e80", strokeWidth: 1.5 },
  })), [stages]);

  const activeSteps = journeySteps.filter((step) => step.personaId === selectedPersona);

  return (
    <div className="page page-journey">
      <section className="page-heading heading-with-action">
        <div>
          <div className="breadcrumb"><span>Campaigns</span><ChevronRight size={13} />NestWise · Summer acquisition<ChevronRight size={13} />Journey</div>
          <h1>Connected campaign journey</h1>
          <p>Inspect what Shogun planned, generated, and checked. Every stage leaves a decision trail.</p>
        </div>
        <button type="button" className="primary-button compact" onClick={onOpenCreative}>Review 9 variants <ArrowRight size={15} /></button>
      </section>

      <div className="workflow-layout">
        <section className="panel workflow-canvas-panel">
          <div className="panel-topline">
            <div><span className="eyebrow">Workflow map</span><h2>Plan → review → adapt</h2></div>
            <div className="legend"><span><i className="complete" />Complete</span><span><i className="warning" />Review</span><span><i className="pending" />Pending</span></div>
          </div>
          <div className="workflow-canvas">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodeClick={(_, node) => setSelectedStageId(node.id)}
              fitView
              fitViewOptions={{ padding: 0.14 }}
              minZoom={0.55}
              maxZoom={1.1}
              nodesDraggable={false}
              nodesConnectable={false}
              elementsSelectable
              panOnDrag
              zoomOnScroll={false}
              proOptions={{ hideAttribution: true }}
            >
              <Background color="#dad9d1" gap={22} size={1} variant={BackgroundVariant.Dots} />
            </ReactFlow>
          </div>
        </section>

        <aside className="panel stage-inspector">
          <div className="inspector-header">
            <span className={`inspector-status ${selectedStage.status}`}>
              {selectedStage.status === "completed" ? <Check size={15} /> : selectedStage.status === "approval_required" ? <Clock3 size={15} /> : <Sparkles size={15} />}
            </span>
            <div><span className="eyebrow">{selectedStage.eyebrow}</span><h2>{selectedStage.label}</h2></div>
          </div>
          <span className={`status-label label-${selectedStage.status}`}>{selectedStage.status.replace("_", " ")}</span>
          <p className="inspector-summary">{selectedStage.summary}</p>
          <div className="inspector-divider" />
          <h3>Stage output</h3>
          <div className="output-list">
            {selectedStage.id === "approval" ? <>
              <div><span>Blocking findings</span><strong className="success-text">0 open</strong></div>
              <div><span>Advisory notes</span><strong>1 open</strong></div>
              <div><span>Current revisions</span><strong>9 variants</strong></div>
            </> : <>
              <div><span>Personas mapped</span><strong>3 / 3</strong></div>
              <div><span>Channels covered</span><strong>3 / 3</strong></div>
              <div><span>Last updated</span><strong>Just now</strong></div>
            </>}
          </div>
          <div className="inspector-callout"><ShieldAlert size={16} /><div><strong>Policy-readiness, not compliance</strong><p>Final legal and platform review remains human-owned.</p></div></div>
          <button type="button" className="text-button" onClick={onOpenCreative}>Inspect stage output <ArrowRight size={14} /></button>
        </aside>
      </div>

      <div className="strategy-grid">
        <section className="panel persona-panel">
          <div className="panel-topline"><div><span className="eyebrow">Strategy output</span><h2>Audience personas</h2></div><span className="count-badge">3 synthetic segments</span></div>
          <div className="persona-cards">
            {personas.map((persona, index) => (
              <button type="button" className={`persona-card ${selectedPersona === persona.id ? "selected" : ""}`} onClick={() => setSelectedPersona(persona.id)} key={persona.id}>
                <div className="persona-card-top"><span className="persona-avatar" style={{ background: persona.accent }}>{persona.shortName.slice(0, 1)}</span><span className={`risk-tag risk-${persona.riskSensitivity}`}>{persona.riskSensitivity} sensitivity</span></div>
                <span className="persona-number">P0{index + 1}</span><h3>{persona.name}</h3><p>{persona.summary}</p>
                <div className="persona-trigger"><Target size={13} /><span>{persona.decisionTrigger}</span></div>
              </button>
            ))}
          </div>
        </section>

        <section className="panel kpi-panel">
          <div className="panel-topline"><div><span className="eyebrow">Committed measures</span><h2>Campaign KPIs</h2></div><span className="count-badge">Pre-generation</span></div>
          <div className="kpi-cards">
            {kpis.map((kpi) => <div className="kpi-card" key={kpi.id}><div><span className="kpi-trend">↗</span><strong>{kpi.target}</strong></div><h3>{kpi.name}</h3><p>{kpi.measurement}</p></div>)}
          </div>
        </section>
      </div>

      <section className="panel matrix-panel">
        <div className="panel-topline">
          <div><span className="eyebrow">Cross-channel plan</span><h2>{personas.find((persona) => persona.id === selectedPersona)?.shortName}’s connected journey</h2></div>
          <span className="allocation-total">{activeSteps.reduce((sum, step) => sum + step.allocationPercent, 0)}% of Wave 1 allocation</span>
        </div>
        <div className="journey-table-wrap"><table className="journey-table"><thead><tr><th>Channel</th><th>Journey stage</th><th>Message angle</th><th>Primary measure</th><th>Allocation</th></tr></thead><tbody>
          {activeSteps.map((step) => {
            const Icon = step.channel === "google_search" ? Search : step.channel === "email" ? Mail : Megaphone;
            return <tr key={step.id}><td><span className={`channel-icon channel-${step.channel}`}><Icon size={15} /></span><strong>{channelLabels[step.channel]}</strong></td><td><span className="stage-chip">{step.journeyStage}</span></td><td>{step.messageAngle}</td><td>{kpis.find((kpi) => kpi.id === step.primaryKpiId)?.name}</td><td><div className="allocation-cell"><span style={{ width: `${step.allocationPercent * 4}px` }} />{step.allocationPercent}%</div></td></tr>;
          })}
        </tbody></table></div>
      </section>
      {status === "running" && <div className="running-banner"><Sparkles size={16} /> Shogun is advancing through the cached workflow. Select any completed node to inspect it.</div>}
    </div>
  );
}
