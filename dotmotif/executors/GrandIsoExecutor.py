"""
Copyright 2021 The Johns Hopkins University Applied Physics Laboratory.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.`
"""
from functools import lru_cache
from typing import Optional
import networkx as nx
from grandiso import find_motifs_iter

from .NetworkXExecutor import NetworkXExecutor, _node_satisfies_constraints


class GrandIsoExecutor(NetworkXExecutor):
    """
    A DotMotif executor that uses grandiso for subgraph monomorphism.

    This executor is dramatically fast than the NetworkX search, and is still
    a pure-Python implementation.

    [GrandIso](https://github.com/aplbrain/grandiso-networkx)

    """

    def find(self, motif, limit: Optional[int] = None):
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.Motif)
            limit (int: None)

        Returns:
            List[dict]

        """
        # We need to first remove "negative" nodes from the motif, and then
        # filter them out later on.

        if motif.ignore_direction or not self.graph.is_directed:  # type: ignore
            graph_constructor = nx.Graph
        else:
            graph_constructor = nx.DiGraph

        only_positive_edges_motif = graph_constructor()
        must_not_exist_edges = []
        for u, v, attrs in motif.to_nx().edges(data=True):
            if attrs["exists"] is True:
                only_positive_edges_motif.add_edge(u, v, **attrs)
            elif attrs["exists"] is False:
                # Collect a list of neg-edges to check for again in a moment
                must_not_exist_edges.append((u, v))

        def _doesnt_have_any_of_motifs_negative_edges(mapping):
            for u, v in must_not_exist_edges:
                if self.graph.has_edge(mapping[u], mapping[v]):  # type: ignore
                    return False
            return True

        constraints = motif.list_node_constraints()

        @lru_cache()
        def _node_attr_match_fn(
            motif_node_id: str, host_node_id: str, motif_nx: nx.Graph, host_nx: nx.Graph
        ):
            return _node_satisfies_constraints(
                host_nx.nodes[host_node_id], constraints.get(motif_node_id, {})
            )
            return True

        graph_matches = find_motifs_iter(
            only_positive_edges_motif,
            self.graph,
            is_node_attr_match=_node_attr_match_fn,
            is_edge_attr_match=lambda _1, _2, _3, _4: True,
        )

        _edge_constraint_validator = (
            self._validate_edge_constraints
            if not self._host_is_multigraph
            else (
                self._validate_multigraph_all_edge_constraints
                if self._multigraph_edge_match == "all"
                else self._validate_multigraph_any_edge_constraints
            )
        )
        _edge_dynamic_constraint_validator = self._validate_dynamic_edge_constraints

        results = []
        for r in graph_matches:
            if _doesnt_have_any_of_motifs_negative_edges(r) and (
                _edge_constraint_validator(r, self.graph, motif.list_edge_constraints())
                and _edge_dynamic_constraint_validator(
                    r, self.graph, motif.list_dynamic_edge_constraints()
                )
                and self._validate_dynamic_node_constraints(
                    r, self.graph, motif.list_dynamic_node_constraints()
                )
                # by default, networkx returns the automorphism that is left-
                # sorted, so this comparison is _opposite_ the check that we
                # use in the other executors. In other words, we usually check
                # that A >= B; here we check A <= B.
                and (
                    (not motif.exclude_automorphisms)
                    or all(r[a] <= r[b] for (a, b) in motif.list_automorphisms())
                )
            ):
                results.append(r)
                if limit and len(results) >= limit:
                    return results

        return results
