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
    parents: list[NodeReference]
    children: list[NodeReference]


AdjacencyList = list[AdjacencyListRecord]


@dataclass
class TraceRecord:
    timestamp: datetime
    role: Literal["user", "assistant"]
    content: str | None
    reasoning_content: str | None
    cost: float | None


@dataclass
class HypothesisValidationResult:
    decision: Literal["accept", "refine", "reject"]
    explanation: str
    new_hypothesis: str | None


@dataclass
class ActionsImpl:
    get_similar_nodes: Callable[[str], AdjacencyList]
    get_parents: Callable[[str, int], AdjacencyList]
    get_children: Callable[[str, int], AdjacencyList]
    get_causal_chain: Callable[[str, str], AdjacencyList]
    connect_nodes: Callable[[str, str], None]
