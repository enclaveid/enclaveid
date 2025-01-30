from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Literal


@dataclass
class NodeReference:
    id: str
    datetime: str


@dataclass
class AdjacencyListRecord:
    id: str
    description: str
    datetime: str
    frequency: int
    parents_count: int
    children_count: int
    # parents: list[NodeReference]
    # children: list[NodeReference]


AdjacencyList = list[AdjacencyListRecord]


@dataclass
class TraceRecord:
    timestamp: datetime
    role: Literal["user", "assistant"]
    content: str | None
    reasoning_content: str | None
    cost: float | None
    token_count: int | None


@dataclass
class HypothesisValidationResult:
    decision: Literal["accept", "refine", "reject"]
    explanation: str
    new_hypothesis: str | None = None


@dataclass
class ActionsImpl:
    get_similar_nodes: Callable[[str], AdjacencyList]
    get_causes: Callable[[str], AdjacencyList]
    get_effects: Callable[[str, int], AdjacencyList]
    get_causal_chain: Callable[[str, str], AdjacencyList]


@dataclass
class ActionResult:
    action: str
    args: dict
    result: AdjacencyList
