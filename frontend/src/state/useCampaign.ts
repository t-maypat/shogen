import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { subscribeToCampaign } from "../api/events";
import { adaptCampaignState, STAGE_TEMPLATE, type AdaptedCampaignState } from "../api/adapt";
import type { CampaignStatus, ConnectionState, WorkflowEvent, WorkflowStage } from "../types";

const STORAGE_KEY = "shogen.campaignId";

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

const CHECKPOINT_EVENT_TYPES = new Set([
  "stage.completed",
  "policy.failed",
  "approval.required",
  "approval.completed",
  "mock_deployment.completed",
  "evaluation.completed",
  "wave2.completed",
  "workflow.completed",
  "workflow.failed",
]);

export function useCampaign() {
  const [campaignId, setCampaignId] = useState<string | null>(null);
  const [state, setState] = useState<AdaptedCampaignState | null>(null);
  const [stages, setStages] = useState<WorkflowStage[]>(() => STAGE_TEMPLATE.map((stage) => ({ ...stage })));
  const [status, setStatus] = useState<CampaignStatus>("draft");
  const [connection, setConnection] = useState<ConnectionState>("idle");
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);
  // The backend closes the SSE stream as soon as the run is no longer "running"
  // (i.e. it pauses at approval_required or finishes). That close fires
  // EventSource.onerror even though nothing failed. This ref lets onError tell a
  // clean end-of-stream from a real connection drop (backend died mid-run).
  const expectStreamEndRef = useRef(false);

  const refetch = useCallback(async (id: string) => {
    const raw = await api.getCampaign(id);
    const adapted = adaptCampaignState(raw);
    setState(adapted);
    setStages(adapted.stages);
    setStatus(adapted.status);
    return adapted;
  }, []);

  const setNodeStatus = useCallback((nodeId: string | undefined, nextStatus: WorkflowStage["status"]) => {
    if (!nodeId) return;
    setStages((current) => current.map((stage) => (stage.id === nodeId ? { ...stage, status: nextStatus } : stage)));
  }, []);

  const subscribe = useCallback(
    (id: string) => {
      unsubscribeRef.current?.();
      expectStreamEndRef.current = false;
      unsubscribeRef.current = subscribeToCampaign(
        id,
        (event: WorkflowEvent) => {
          setConnection("live");
          const nodeId = event.stage ? STAGE_TO_NODE[event.stage] : undefined;

          // The run stops streaming once it pauses for approval or completes.
          // Mark that so the imminent stream close isn't reported as an error.
          if (event.eventType === "approval.required" || event.eventType === "workflow.completed") {
            expectStreamEndRef.current = true;
          }

          switch (event.eventType) {
            case "stage.started":
              setNodeStatus(nodeId, "running");
              break;
            case "stage.completed":
              setNodeStatus(nodeId, "completed");
              if (event.stage === "policy") setNodeStatus("semantic", "completed");
              break;
            case "approval.required":
              setNodeStatus("approval", "approval_required");
              break;
            case "mock_deployment.completed":
              setNodeStatus("deploy", "completed");
              break;
            case "evaluation.completed":
              setNodeStatus("evaluation", "completed");
              break;
            case "wave2.completed":
              setNodeStatus("wave2", "completed");
              break;
            case "policy.failed":
              setNodeStatus("policy", "failed");
              setNodeStatus("semantic", "failed");
              break;
            case "workflow.failed":
              setNodeStatus(nodeId, "failed");
              break;
            default:
              break;
          }

          if (CHECKPOINT_EVENT_TYPES.has(event.eventType)) {
            void refetch(id).catch(() => setConnection("error"));
          }
        },
        () => {
          setConnection("live");
          void refetch(id).catch(() => setConnection("error"));
        },
        () => {
          if (expectStreamEndRef.current) {
            // Clean end-of-stream (approval pause / completion). Close our handle
            // so EventSource doesn't keep retrying against a stream that the
            // backend will immediately close again, and stay "live".
            setConnection("live");
            unsubscribeRef.current?.();
            unsubscribeRef.current = null;
          } else {
            setConnection("error");
          }
        },
      );
    },
    [refetch, setNodeStatus],
  );

  const startReplay = useCallback(async () => {
    setError(null);
    try {
      const result = await api.startReplay();
      setCampaignId(result.campaign_id);
      window.localStorage.setItem(STORAGE_KEY, result.campaign_id);
      await refetch(result.campaign_id);
      subscribe(result.campaign_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the replay.");
      setConnection("error");
    }
  }, [refetch, subscribe]);

  const approve = useCallback(async () => {
    if (!campaignId) return;
    setApproving(true);
    setError(null);
    try {
      await api.approveCampaign(campaignId);
      await refetch(campaignId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed.");
    } finally {
      setApproving(false);
    }
  }, [campaignId, refetch]);

  const retry = useCallback(() => {
    setError(null);
    setConnection("idle");
    if (!campaignId) return Promise.resolve(undefined);
    return refetch(campaignId).catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "Could not reach Shogun.");
      setConnection("error");
    });
  }, [campaignId, refetch]);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return;
    setCampaignId(stored);
    refetch(stored)
      .then((adapted) => {
        if (adapted.latestRun?.status === "running") {
          subscribe(stored);
        }
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Could not reach Shogun.");
        setConnection("error");
      });
  }, [refetch, subscribe]);

  useEffect(() => () => unsubscribeRef.current?.(), []);

  return {
    campaignId,
    state,
    stages,
    status,
    connection,
    approving,
    error,
    startReplay,
    approve,
    retry,
  };
}
