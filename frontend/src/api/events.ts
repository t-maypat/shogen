import { API_BASE_URL } from "./client";
import type { WorkflowEvent } from "../types";

export function subscribeToCampaign(
  campaignId: string,
  onEvent: (event: WorkflowEvent) => void,
  onReconnect?: () => void,
) {
  const source = new EventSource(`${API_BASE_URL}/api/campaigns/${campaignId}/events`);
  const handle = (message: MessageEvent<string>) => onEvent(JSON.parse(message.data) as WorkflowEvent);

  ["stage.started", "stage.completed", "policy.failed", "approval.required", "approval.completed", "evaluation.completed", "wave2.completed", "workflow.completed"].forEach(
    (event) => source.addEventListener(event, handle as EventListener),
  );
  source.onopen = () => onReconnect?.();
  return () => source.close();
}
