import os

IS_CAUSAL_GRAPH_ENABLED = os.getenv("FEATURE_FLAG_CAUSAL_GRAPH", "false") == "true"

IS_AI_CONVERSATIONS_ENABLED = (
    os.getenv("FEATURE_FLAG_AI_CONVERSATIONS", "false") == "true"
)

IS_HUMAN_CONVERSATIONS_ENABLED = (
    os.getenv("FEATURE_FLAG_HUMAN_CONVERSATIONS", "true") == "true"
)
