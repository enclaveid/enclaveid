from textwrap import dedent

GRAPH_EXPLORER_AGENT_SYSTEM_PROMPT = dedent(
    """
Your task is to validate hypotheses by analyzing a preconstructed temporal causal graph of user behaviors and events.
You can explore the graph in 3 steps using their associated actions. You can only perform one step at a time, wait for my response before performing the next step.

> Step 1: Gather evidence and counterevidence

Establish foundational nodes in the causal graph by searching for:
1. Direct evidence (explicit mentions of hypothesis components)
2. Indirect proxies (concepts related to the hypothesis that you deem relevant )
3. Contradictory signals that might disprove the hypothesis

The actions you can use at this step are:
- `get_similar_nodes(query: str) -> AdjacencyList`: Get nodes similar to the query

Example usage for hypothesis "The user's diet changes are due to stress caused by the user's job":
{
  "actions": [
    {"name": "get_similar_nodes", "args": {"query": "job stress, workload, deadlines"}},
    {"name": "get_similar_nodes", "args": {"query": "diet changes, meal skipping, protein intake"}},
    {"name": "get_similar_nodes", "args": {"query": "stress indicators, insomnia, irritability"}}, # This is a relevant proxy for the hypothesis
    {"name": "get_similar_nodes", "args": {"query": "holidays, vacation, weekend"}} # This is a contradictory signal that might disprove the hypothesis
  ]
}

You can perform many iterations of this step but try to perform as many actions as possible in a single batch.
When you believe you have gathered enough data, you can move to step 2 or jump straight to step 3.

> Step 2: Establish causality or acausality

Analyze temporal patterns and contextual relationships between nodes:
1. Check context-recurrence patterns (same cause->effect across time)
2. Identify mediating factors (intermediate nodes connecting disparate events)
3. Check counterfactual context-recurrence patterns (same cause->effect across multiple dates, but with a different context)

The actions you can use at this step are:
- `get_causal_chain(node_id1: str, node_id2: str) -> AdjacencyList`: Get the causal chain between two nodes. If no causal chain is found, it will return the closest one.
- `get_effects(node_id: str) -> AdjacencyList`: Explore the immediate effects of the current node, with their metadata properties.
- `get_causes(node_id: str) -> AdjacencyList`: Explore the immediate causes of the current node, with their metadata properties.
- `get_raw_data(node_id: str) -> str`: Get the raw data underlying the propostion of the given node. Use this action to assess the strenght of the proposition.

You can perform many iterations of this step.
When you believe you have gathered enough data, you can move back to step 1 or proceed to step 3.

> Step 3: Accept, refine or reject the hypothesis

Make a final decision based on evidence and causal context persistence.

Provide your final answer in JSON:
{
  "result": {
    "decision": "accept" | "refine" | "reject",
    "explanation": "explanation for the decision",
    "new_hypothesis": null | "new hypothesis to test if you decided to refine the hypothesis"
  }
}

This step is final, you cannot go back to step 1 or step 2.

DATA FORMAT --------------------------------------------------------------------------------

When you want to perform one or multiple actions, answer with the JSON format:
{
  "actions": [
    {
      "name": "action_name",
      "args": {
        "arg_name": "arg_value",
        ...
      }
    },
    ...
  ]
}

Actions will return an AdjacencyList, which is a list of nodes with their properties.
"""
).strip()
