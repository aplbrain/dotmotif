from typing import TYPE_CHECKING
import networkx as nx
import pandas as pd

from .Executor import Executor

if TYPE_CHECKING:
    from .. import dotmotif


def _edge_satisfies_constraints(edge_attributes: dict, constraints: dict) -> bool:
    """
    Check if a single edge satisfies the constraints.
    """

    operators = {
        "=": lambda x, y: x == y,
        "==": lambda x, y: x == y,
        ">=": lambda x, y: x >= y,
        "<=": lambda x, y: x <= y,
        "<": lambda x, y: x < y,
        ">": lambda x, y: x > y,
        "!=": lambda x, y: x != y,
        "in": lambda x, y: x in y,
        "contains": lambda x, y: y in x,
    }

    for key, clist in constraints.items():
        for operator, values in clist.items():
            for value in values:
                keyvalue_or_none = edge_attributes.get(key, None)
                try:
                    operator_success = operators[operator](keyvalue_or_none, value)
                except TypeError:
                    # If you encounter a type error, that means the comparison
                    # could not possibly succeed,
                    # # TODO: unless you tried a comparison
                    # against an undefined value (i.e. VALUE >= undefined)
                    return False
                if not operator_success:
                    # Fail fast, if any edge attributes fail the test
                    return False
    return True


def _node_satisfies_constraints(node_attributes: dict, constraints: dict) -> bool:
    """
    Check if a single node satisfies the constraints.

    TODO: This function is distinct from the above because I anticipate that
    differences will emerge as the implementation matures. But these are
    currently identical functions otherwise. -- @j6k4m8 Jan 2019
    """

    operators = {
        "=": lambda x, y: x == y,
        "==": lambda x, y: x == y,
        ">=": lambda x, y: x >= y,
        "<=": lambda x, y: x <= y,
        "<": lambda x, y: x < y,
        ">": lambda x, y: x > y,
        "!=": lambda x, y: x != y,
        "in": lambda x, y: x in y,
        "contains": lambda x, y: y in x,
    }

    for key, clist in constraints.items():
        for operator, values in clist.items():
            for value in values:
                if not operators[operator](node_attributes.get(key, None), value):
                    # Fail fast, if any node attributes fail the test
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

    def _validate_node_constraints(
        self, node_isomorphism_map: dict, graph: nx.DiGraph, constraints: dict
    ) -> bool:
        """
        Validate nodes against their isomorphism's constraints in the motif.

        Arguments:
            ...

        Returns:
            bool
        """
        for motif_U, constraint_list in constraints.items():
            graph_u = node_isomorphism_map[motif_U]

            if not _node_satisfies_constraints(graph.nodes[graph_u], constraint_list):
                return False
        return True

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
            edge_attrs = graph.get_edge_data(graph_u, graph_v)

            if not _edge_satisfies_constraints(edge_attrs, constraint_list):
                # Fail fast
                return False
        return True

    def count(self, motif: "dotmotif", limit: int = None):
        """
        Count the occurrences of a motif in a graph.

        See NetworkXExecutor#find for more documentation.
        """
        return len(self.find(motif, limit))

    def find(self, motif: "dotmotif", limit: int = None):
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif)

        """
        # TODO: Can add constraints on iso node assignment. If we do this a
        # little smarter, can save a lot of post-processing time-complexity.

        # We need to first remove "negative" nodes from the motif, and then
        # filter them out later on. Though this reduces the speed of the graph-
        # matching, NetworkX does not seem to support this out of the box.
        # TODO: Confirm that networkx does not support this out of the box.

        if motif.ignore_direction or not self.graph.is_directed:
            graph_constructor = nx.Graph
            graph_matcher = nx.algorithms.isomorphism.GraphMatcher
        else:
            graph_constructor = nx.DiGraph
            graph_matcher = nx.algorithms.isomorphism.DiGraphMatcher

        only_positive_edges_motif = graph_constructor()
        must_not_exist_edges = []
        for u, v, attrs in motif.to_nx().edges(data=True):
            if attrs["exists"] is True:
                only_positive_edges_motif.add_edge(u, v, **attrs)
            elif attrs["exists"] is False:
                # Collect a list of neg-edges to check for again in a moment
                must_not_exist_edges.append((u, v))
        gm = graph_matcher(self.graph, only_positive_edges_motif)

        def _doesnt_have_any_of_motifs_negative_edges(mapping):
            for u, v in must_not_exist_edges:
                if self.graph.has_edge(mapping[u], mapping[v]):
                    return False
            return True

        unfiltered_results = [
            # Here, `mapping` has keys of self.graph node IDs and values of
            # motif node names. We need the reverse for pretty much everything
            # we do from here out, so we reverse the pairs.
            {v: k for k, v in mapping.items()}
            for mapping in gm.subgraph_monomorphisms_iter()
        ]

        # Now, filter out those that have edges they should not:
        results = [
            mapping
            for mapping in unfiltered_results
            if _doesnt_have_any_of_motifs_negative_edges(mapping)
        ]

        # Now, filter on attributes:
        res = [
            r
            for r in results
            if (
                self._validate_edge_constraints(
                    r, self.graph, motif.list_edge_constraints()
                )
                and self._validate_node_constraints(
                    r, self.graph, motif.list_node_constraints()
                )
                # by default, networkx returns the automorphism that is left-
                # sorted, so this comparison is _opposite_ the check that we
                # use in the other executors. In other words, we usually check
                # that A >= B; here we check A <= B.
                and (
                    (not motif.exclude_automorphisms)
                    or all(r[a] <= r[b] for (a, b) in motif.list_automorphisms())
                )
            )
        ]
        return res
