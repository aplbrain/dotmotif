import networkx as nx
import pandas as pd

from .Executor import Executor
from .. import dotmotif


class NetworkXExecutor(Executor):
    """
    A query executor that runs inside RAM.

    Uses NetworkX's built-in (VF2) subgraph isomorphism algo. Good for very
    small graphs, since this won't scale particularly well.
    """

    def __init__(self, **kwargs) -> None:
        """
        Create a new NetworkXExecutor.

        Arguments:
            graph (networkx.Graph)

        Returns:
            None

        """
        if "graph" in kwargs:
            self.graph = kwargs.get("graph")
        else:
            raise ValueError(
                "You must pass a graph to the NetworkXExecutor constructor."
            )

    def find(self, motif: dotmotif, limit: int = None):
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif)

        """
        gm = nx.algorithms.isomorphism.GraphMatcher(self.graph, motif.to_nx())
        res = gm.subgraph_isomorphisms_iter()
        return pd.DataFrame([{v: k for k, v in r.items()} for r in res])
