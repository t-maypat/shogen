import { API_BASE_URL } from "./client";
import type { WorkflowEvent } from "../types";

const EVENT_TYPES = [
  "workflow.started",
  "stage.started",
  "stage.completed",
  "policy.failed",
  "policy.revision_created",
  "approval.required",
  "approval.completed",
  "mock_deployment.completed",
  "evaluation.completed",
  "wave2.completed",
  "workflow.completed",
  "workflow.failed",
];

export function subscribeToCampaign(
  campaignId: string,
  onEvent: (event: WorkflowEvent) => void,
  onReconnect?: () => void,
  onError?: () => void,
) {
  const source = new EventSource(`${API_BASE_URL}/api/campaigns/${campaignId}/events`);
  const handle = (message: MessageEvent<string>) => {
    const data = JSON.parse(message.data) as Omit<WorkflowEvent, "eventType">;
    onEvent({ ...data, eventType: message.type });
  };

  EVENT_TYPES.forEach((event) => source.addEventListener(event, handle as EventListener));
  source.onopen = () => onReconnect?.();
  source.onerror = () => onError?.();
  return () => source.close();
}
