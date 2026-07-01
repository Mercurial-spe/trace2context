from dataclasses import dataclass, field

from trace2context.trace.schema import TraceEvent


@dataclass
class AgentRun:
    """Container for the minimal agent loop state.

    The first implementation milestone uses offline traces. A real LLM loop can
    attach to this class without changing analyzer/filter contracts.
    """

    run_id: str
    events: list[TraceEvent] = field(default_factory=list)

    def append(self, event: TraceEvent) -> None:
        self.events.append(event)
