from logging import Logger

from dagster import (
    ConfigurableResource,
    DagsterLogManager,
    InitResourceContext,
    get_dagster_logger,
)
from pydantic import PrivateAttr

from data_pipeline.resources.graph_explorer_agent.agent import (
    GraphExplorerAgent,
)
from data_pipeline.resources.graph_explorer_agent.types import ActionsImpl


class GraphExplorerAgentResource(ConfigurableResource):
    api_key: str

    _agent: GraphExplorerAgent = PrivateAttr()
    _logger: DagsterLogManager | Logger = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._agent = GraphExplorerAgent(
            api_key=self.api_key,
        )
        self._logger = context.log or get_dagster_logger()

    def validate_hypothesis(self, hypothesis: str, actions_impl: ActionsImpl):
        return self._agent.validate_hypothesis(hypothesis, actions_impl)
