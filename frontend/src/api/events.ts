import { API_BASE_URL } from "./client";
import type { WorkflowEvent } from "../types";

export function subscribeToCampaign(
  campaignId: string,
  onEvent: (event: WorkflowEvent) => void,
  onReconnect?: () => void,
) {
  const source = new EventSource(`${API_BASE_URL}/api/campaigns/${campaignId}/events`);

  const handle = (sseEventName: string) => (message: MessageEvent<string>) => {
    const data = JSON.parse(message.data) as Omit<WorkflowEvent, "eventType">;
    onEvent({ ...data, eventType: sseEventName });
  };

  [
    "workflow.started",
    "stage.started",
    "stage.completed",
    "policy.failed",
    "policy.revision_created",
    "approval.completed",
    "mock_deployment.completed",
    "evaluation.completed",
    "wave2.completed",
    "workflow.completed",
    "workflow.failed",
  ].forEach((event) =>
    source.addEventListener(event, handle(event) as EventListener),
  );

  source.onopen = () => onReconnect?.();
  return () => source.close();
}
