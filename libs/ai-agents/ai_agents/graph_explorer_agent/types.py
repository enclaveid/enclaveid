from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Literal


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
class HypothesisValidationResult:
    decision: Literal["accept", "refine", "reject"]
    explanation: str
    new_hypothesis: str | None = None


@dataclass
class ActionsImpl:
    get_similar_nodes: Callable[[str], Coroutine[Any, Any, AdjacencyList]]
    get_causes: Callable[[str], AdjacencyList]
    get_effects: Callable[[str, int], AdjacencyList]
    get_causal_chain: Callable[[str, str], AdjacencyList]
    get_raw_data: Callable[[str], str]


@dataclass
class ActionResult:
    action: str
    args: dict
    result: AdjacencyList
