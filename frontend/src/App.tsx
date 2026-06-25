import { useState, useEffect, useRef } from "react";
import { AppHeader } from "./components/AppHeader";
import { ActivityPanel } from "./components/ActivityPanel";
import { BriefTab } from "./components/brief/BriefTab";
import { JourneyTab } from "./components/journey/JourneyTab";
import { CreativeTab } from "./components/creative/CreativeTab";
import { ResultsTab } from "./components/results/ResultsTab";
import { blankBrief, completedStages, demoBrief, kpis } from "./data/demo";
import { api } from "./api/client";
import { subscribeToCampaign } from "./api/events";
import type { CampaignStatus, TabId, WorkflowStage, CampaignBrief, WorkflowEvent } from "./types";

const backendToFrontendStage = (backendStage: string): string => {
  if (backendStage === "mock_deployment") return "deploy";
  return backendStage;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("brief");
  const [status, setStatus] = useState<CampaignStatus>("draft");
  const [stages, setStages] = useState<WorkflowStage[]>(completedStages);
  const [activityOpen, setActivityOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [campaignId, setCampaignId] = useState<string | null>(null);
  const [briefKey, setBriefKey] = useState(0);
  const [briefData, setBriefData] = useState<CampaignBrief>(demoBrief);
  const unsubRef = useRef<(() => void) | null>(null);

  const toast = (message: string) => {
    setNotice(message);
    window.setTimeout(() => setNotice(null), 3600);
  };

  const createNewCampaign = () => {
    setBriefData(blankBrief);
    setBriefKey((k) => k + 1);
    setActiveTab("brief");
    setStatus("draft");
    toast("Blank campaign started");
  };

  const updateStage = (id: string, nextStatus: WorkflowStage["status"]) => {
    setStages((current) => current.map((stage) => stage.id === id ? { ...stage, status: nextStatus } : stage));
  };

  // Subscribe to SSE whenever campaignId changes
  useEffect(() => {
    if (!campaignId) return;

    // Clean up previous subscription
    unsubRef.current?.();

    const unsubscribe = subscribeToCampaign(
      campaignId,
      (event: WorkflowEvent) => {
        switch (event.eventType) {
          case "workflow.started":
            setStatus("running");
            break;

          case "stage.started":
            if (event.stage) {
              updateStage(backendToFrontendStage(event.stage), "running");
              if (event.stage === "evaluation") setStatus("evaluating");
            }
            break;

          case "stage.completed":
            if (event.stage) {
              if (event.stage === "approval_required") {
                // The approval gate emits stage.completed with stage="approval_required"
                setStatus("approval_required");
                updateStage("approval", "approval_required");
                toast("Creative is policy-ready and waiting for approval");
              } else {
                updateStage(backendToFrontendStage(event.stage), "completed");
                if (event.stage === "policy") {
                  updateStage("semantic", "completed");
                }
              }
            }
            break;

          case "policy.failed":
            updateStage("policy", "warning");
            break;

          case "mock_deployment.completed":
            updateStage("deploy", "completed");
            break;

          case "approval.completed":
            setStatus("approved");
            updateStage("approval", "completed");
            toast("Campaign approved for mock deployment");
            break;

          case "evaluation.completed":
            updateStage("evaluation", "completed");
            break;

          case "wave2.completed":
            updateStage("wave2", "completed");
            break;

          case "workflow.completed":
            setStatus("completed");
            setActiveTab("results");
            toast("Wave 2 recommendation is ready");
            break;

          case "workflow.failed":
            setStatus("failed");
            if (event.stage) updateStage(backendToFrontendStage(event.stage), "failed");
            toast("Workflow failed");
            break;
        }
      },
      () => {
        console.log("SSE reconnected");
      }
    );

    unsubRef.current = unsubscribe;
    return unsubscribe;
  }, [campaignId]);

  const initStages = () => {
    setStages(completedStages.map((stage, index) => ({ ...stage, status: index === 0 ? "completed" : "pending" })));
  }

  // Bug 4 fix: startReplay already kicks off the workflow thread on the backend,
  // so we only need to set the campaignId (which triggers the SSE subscription).
  // No separate runCampaign call is needed.
  const runReplay = async () => {
    if (status === "running" || status === "evaluating") return;
    try {
      initStages();
      setStatus("running");
      setActiveTab("journey");
      toast("Golden fintech replay started");
      const res = await api.startReplay();
      setCampaignId(res.campaign_id);
    } catch (err: any) {
      toast(err.message);
      setStatus("failed");
    }
  };

  const startLiveRun = async (brief: CampaignBrief) => {
    if (status === "running" || status === "evaluating") return;
    try {
      initStages();
      setStatus("running");
      setActiveTab("journey");
      toast("Starting live run");

      const createRes = await api.createCampaign(brief);
      setCampaignId(createRes.campaign_id);

      // For live runs, we need to explicitly trigger the workflow
      // (unlike replay which auto-starts in the backend).
      // Small delay to let the SSE subscription connect first.
      setTimeout(() => {
        api.runCampaign(createRes.campaign_id, "live").catch((err) => {
          toast(err.message);
          setStatus("failed");
        });
      }, 500);
    } catch (err: any) {
      toast(err.message);
      setStatus("failed");
    }
  };

  const approve = async () => {
    if (status !== "approval_required" || !campaignId) return;
    try {
      await api.approveCampaign(campaignId);
    } catch (err: any) {
      toast(err.message);
    }
  };

  return (
    <div className="app-shell">
      <AppHeader activeTab={activeTab} status={status} onTabChange={setActiveTab} onOpenActivity={() => setActivityOpen(true)} onToast={toast} onCreateNewCampaign={createNewCampaign} />
      <main className="workspace-main">
        {activeTab === "brief" && <BriefTab key={briefKey} initialBrief={briefData} initialKpis={briefData === blankBrief ? [] : kpis} status={status} onRunReplay={runReplay} onStartLive={startLiveRun} />}
        {activeTab === "journey" && <JourneyTab stages={stages} status={status} onOpenCreative={() => setActiveTab("creative")} />}
        {activeTab === "creative" && <CreativeTab status={status} onApprove={approve} />}
        {activeTab === "results" && <ResultsTab status={status} onReviewCreative={() => setActiveTab("creative")} />}
      </main>
      <ActivityPanel open={activityOpen} stages={stages} onClose={() => setActivityOpen(false)} />
      {notice && <div className="toast" role="status"><span className="toast-mark">S</span>{notice}</div>}
    </div>
  );
}
