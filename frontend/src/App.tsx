import { useState } from "react";
import { AppHeader } from "./components/AppHeader";
import { ActivityPanel } from "./components/ActivityPanel";
import { BriefTab } from "./components/brief/BriefTab";
import { JourneyTab } from "./components/journey/JourneyTab";
import { CreativeTab } from "./components/creative/CreativeTab";
import { ResultsTab } from "./components/results/ResultsTab";
import { completedStages } from "./data/demo";
import type { CampaignStatus, TabId, WorkflowStage } from "./types";

const sleep = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("brief");
  const [status, setStatus] = useState<CampaignStatus>("approval_required");
  const [stages, setStages] = useState<WorkflowStage[]>(completedStages);
  const [activityOpen, setActivityOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const toast = (message: string) => {
    setNotice(message);
    window.setTimeout(() => setNotice(null), 3600);
  };

  const updateStage = (id: string, nextStatus: WorkflowStage["status"]) => {
    setStages((current) => current.map((stage) => stage.id === id ? { ...stage, status: nextStatus } : stage));
  };

  const runReplay = async () => {
    if (status === "running" || status === "evaluating") return;
    setStatus("running");
    setActiveTab("journey");
    setStages(completedStages.map((stage, index) => ({ ...stage, status: index === 0 ? "completed" : "pending" })));
    toast("Golden fintech replay started");
    for (const id of ["strategy", "journey", "creative", "policy", "semantic"]) {
      updateStage(id, "running");
      await sleep(520);
      updateStage(id, id === "policy" ? "warning" : "completed");
    }
    updateStage("approval", "approval_required");
    setStatus("approval_required");
    toast("Creative is policy-ready and waiting for approval");
  };

  const approve = async () => {
    if (status !== "approval_required") return;
    updateStage("approval", "completed");
    setStatus("approved");
    toast("Campaign approved for mock deployment");
    await sleep(450);
    updateStage("deploy", "running");
    await sleep(650);
    updateStage("deploy", "completed");
    setStatus("evaluating");
    updateStage("evaluation", "running");
    await sleep(700);
    updateStage("evaluation", "completed");
    updateStage("wave2", "running");
    await sleep(700);
    updateStage("wave2", "completed");
    setStatus("completed");
    setActiveTab("results");
    toast("Wave 2 recommendation is ready");
  };

  return (
    <div className="app-shell">
      <AppHeader activeTab={activeTab} status={status} onTabChange={setActiveTab} onOpenActivity={() => setActivityOpen(true)} onToast={toast} />
      <main className="workspace-main">
        {activeTab === "brief" && <BriefTab status={status} onRunReplay={runReplay} />}
        {activeTab === "journey" && <JourneyTab stages={stages} status={status} onOpenCreative={() => setActiveTab("creative")} />}
        {activeTab === "creative" && <CreativeTab status={status} onApprove={approve} />}
        {activeTab === "results" && <ResultsTab status={status} onReviewCreative={() => setActiveTab("creative")} />}
      </main>
      <ActivityPanel open={activityOpen} stages={stages} onClose={() => setActivityOpen(false)} />
      {notice && <div className="toast" role="status"><span className="toast-mark">S</span>{notice}</div>}
    </div>
  );
}
