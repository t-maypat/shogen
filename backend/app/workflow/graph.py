from __future__ import annotations

from collections.abc import Callable, Mapping

from app.workflow.state import WorkflowState

STAGE_ORDER = (
    "strategy",
    "journey",
    "creative",
    "policy",
    "approval_required",
)

try:
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised when dependency is installed
    END = "__end__"
    START = "__start__"
    StateGraph = None
    LANGGRAPH_AVAILABLE = False


WorkflowNode = Callable[[WorkflowState], WorkflowState]


class SequentialWorkflowGraph:
    def __init__(self, node_handlers: Mapping[str, WorkflowNode]) -> None:
        self.node_handlers = node_handlers

    def invoke(self, state: WorkflowState) -> WorkflowState:
        next_state = dict(state)
        for stage_name in STAGE_ORDER:
            next_state = self.node_handlers[stage_name](next_state)
        return next_state


def build_placeholder_graph(
    node_handlers: Mapping[str, WorkflowNode],
) -> SequentialWorkflowGraph | object:
    if not LANGGRAPH_AVAILABLE:
        return SequentialWorkflowGraph(node_handlers)

    graph = StateGraph(WorkflowState)
    for stage_name in STAGE_ORDER:
        graph.add_node(stage_name, node_handlers[stage_name])

    graph.add_edge(START, STAGE_ORDER[0])
    for current_stage, next_stage in zip(STAGE_ORDER, STAGE_ORDER[1:]):
        graph.add_edge(current_stage, next_stage)
    graph.add_edge(STAGE_ORDER[-1], END)
    return graph.compile()
