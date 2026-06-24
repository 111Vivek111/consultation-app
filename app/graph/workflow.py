from langgraph.graph import (
    StateGraph,
    END
)

from app.graph.state import (
    GraphState
)

from app.graph.nodes import (
    rewrite_query_node,
    retrieve_node,
    rerank_node
)

workflow = StateGraph(
    GraphState
)

workflow.add_node(
    "rewrite",
    rewrite_query_node
)

workflow.add_node(
    "retrieve",
    retrieve_node
)

workflow.add_node(
    "rerank",
    rerank_node
)


workflow.set_entry_point(
    "rewrite"
)

workflow.add_edge(
    "rewrite",
    "retrieve"
)

workflow.add_edge(
    "retrieve",
    "rerank"
)

workflow.add_edge(
    "rerank",
    END
)

app_graph = workflow.compile()