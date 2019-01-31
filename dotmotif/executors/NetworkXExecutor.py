import networkx as nx
import pandas as pd

from .Executor import Executor
from .. import dotmotif


def _edge_satisfies_constraints(
    edge_attributes: dict, constraints: dict
) -> bool:
        """
        Does a single edge satisfy the constraints?
        """

        operators = {
            "=": lambda x, y: x == y,
            "==": lambda x, y: x == y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
            "<": lambda x, y: x < y,
            ">": lambda x, y: x > y,
            "!=": lambda x, y: x != y,
        }

        for key, clist in constraints.items():
            for operator, values in clist.items():
                for value in values:
                    if not operators[operator](edge_attributes.get(key, None), value):
                        # Fail fast, if any edge attributes fail the test
                        return False
        return True


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

    def _validate_edge_constraints(
        self, node_isomorphism_map: dict, graph: nx.DiGraph, constraints: dict
    ):
        """
        Validate all edge constraints on a subgraph.

        Arguments:
            node_isomorphism_map (dict[nodename:str, nodeID:str]): A mapping of
                node names to node IDs (where name comes from the motif and the
                ID comes from the haystack graph).
            graph (nx.DiGraph): The haystack graph
            constraints (dict[(motif_u, motif_v), dict[operator, value]]): Map
                of constraints on the MOTIF node names.

        Returns:
            bool: If the isomorphism satisfies the edge constraints

        For example, if constraints =
        {
            ("A", "B"): {"weight": { "==": 10 }}
        }

        And node_isomorphism_map =
        {
            "A": "x",
            "B": "y",
        }

        And haystack contains the edge (x, y) with attribute weight=10, then
        this function will return True.

        """
        for (motif_U, motif_V), constraint_list in constraints.items():
            # Get graph nodes (from this isomorphism)
            graph_u = node_isomorphism_map[motif_U]
            graph_v = node_isomorphism_map[motif_V]

            # Check edge in graph for constraints
            edge = list(graph.edges((graph_u, graph_v), data=True))[0]

            if len(edge) == 2:
                edge = edge[0], edge[1], {}

            if not _edge_satisfies_constraints(edge[2], constraint_list):
                # Fail fast
                return False
        return True

    def find(self, motif: dotmotif, limit: int = None):
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif)

        """
        # TODO: Can add constraints on node assignment. If we do this a little
        # smarter, can save a lot of post-processing time-complexity.
        gm = nx.algorithms.isomorphism.GraphMatcher(self.graph, motif.to_nx())
        results = [
            {v: k for k, v in r.items()} for r in gm.subgraph_isomorphisms_iter()
        ]
        return pd.DataFrame(
            [
                r
                for r in results
                if self._validate_edge_constraints(
                    r, self.graph, motif.list_edge_constraints()
                )
            ]
        )
