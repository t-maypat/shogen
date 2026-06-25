import { useEffect, useState } from "react";
import { TriangleAlert } from "lucide-react";
import { AppHeader } from "./components/AppHeader";
import { ActivityPanel } from "./components/ActivityPanel";
import { BriefTab } from "./components/brief/BriefTab";
import { JourneyTab } from "./components/journey/JourneyTab";
import { CreativeTab } from "./components/creative/CreativeTab";
import { ResultsTab } from "./components/results/ResultsTab";
import { useCampaign } from "./state/useCampaign";
import type { TabId } from "./types";

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("brief");
  const [activityOpen, setActivityOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const c = useCampaign();

  const toast = (message: string) => {
    setNotice(message);
    window.setTimeout(() => setNotice(null), 3600);
  };

  const handleRunReplay = () => {
    setActiveTab("journey");
    toast("Golden fintech replay started");
    void c.startReplay();
  };

  const handleApprove = () => {
    void c.approve();
  };

  useEffect(() => {
    if (c.status === "approval_required") toast("Creative is policy-ready and waiting for approval");
    if (c.status === "completed") {
      toast("Wave 2 recommendation is ready");
      setActiveTab("results");
    }
  }, [c.status]);

  useEffect(() => {
    if (c.error) toast(c.error);
  }, [c.error]);

  const hasError = c.connection === "error" || c.status === "failed";
  const errorMessage = c.error ?? c.state?.latestRun?.error?.message ?? "Lost connection to Shogun.";

  return (
    <div className="app-shell">
      <AppHeader
        activeTab={activeTab}
        status={c.status}
        onTabChange={setActiveTab}
        onOpenActivity={() => setActivityOpen(true)}
        onToast={toast}
        replayMode={c.state?.latestRun?.replayMode}
        connection={c.connection}
      />
      {hasError && (
        <div className="error-banner" role="alert">
          <TriangleAlert size={16} />
          <div>
            <strong>Shogun lost touch with the workflow</strong>
            <p>{errorMessage}</p>
          </div>
          <button type="button" onClick={() => void c.retry()}>
            Retry
          </button>
        </div>
      )}
      <main className="workspace-main">
        {activeTab === "brief" && <BriefTab status={c.status} onRunReplay={handleRunReplay} />}
        {activeTab === "journey" && (
          <JourneyTab
            stages={c.stages}
            status={c.status}
            onOpenCreative={() => setActiveTab("creative")}
            personas={c.state?.personas}
            kpis={c.state?.kpis}
            journeySteps={c.state?.journey}
          />
        )}
        {activeTab === "creative" && (
          <CreativeTab
            status={c.status}
            onApprove={handleApprove}
            approving={c.approving}
            variants={c.state?.variants}
            findings={c.state?.findings}
            personas={c.state?.personas}
          />
        )}
        {activeTab === "results" && (
          <ResultsTab
            status={c.status}
            onReviewCreative={() => setActiveTab("creative")}
            personas={c.state?.personas}
            variants={c.state?.variants}
            evaluationScores={c.state?.evaluation}
            allocationChanges={c.state?.wave2.allocationChanges}
            wave2={c.state?.wave2}
          />
        )}
      </main>
      <ActivityPanel open={activityOpen} stages={c.stages} onClose={() => setActivityOpen(false)} />
      {notice && <div className="toast" role="status"><span className="toast-mark">S</span>{notice}</div>}
    </div>
  );
}
