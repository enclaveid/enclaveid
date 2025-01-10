import os

IS_CAUSAL_GRAPH_ENABLED = os.getenv("IS_CAUSAL_GRAPH_ENABLED", "false") == "true"
