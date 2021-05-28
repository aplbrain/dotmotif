"""
Copyright 2020 The Johns Hopkins University Applied Physics Laboratory.

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

import networkx as nx
from grandiso import find_motifs_iter

from .NetworkXExecutor import NetworkXExecutor, _node_satisfies_constraints


class GrandIsoBruteForceExecutor(NetworkXExecutor):
    def find(self, motif, limit: int = None):
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

        # Two important notes, if you're planning on messing with this method:
        # The first: The function signature of the `grandiso.find_motifs` call
        # is the reverse of the NetworkX signature. In other words, in networkx
        # you call (host, motif). In GrandIso, you call (motif, host). This is
        # intentional because it enables better partial function calls that
        # reuse the same motif, which -- if you're using Grand at least --
        # means that you're avoiding having to serialize the heavy Host graph.
        # But it is sorta confusing. Not clear if it's going to stay that way,
        # but for now it's hardly worth the trouble.
        # The second important note is that GrandIso decides for itself whether
        # it's going to be able to perform a directed or undirected motif
        # search; the user doesn't get to decide. (After all, the user
        # shouldn't have the option to request a poorly defined operation. APIs
        # should be smart enough to know what you want while avoiding adding
        # complexity. Anyway, soapbox over.) To that end, this confirmation
        # that the motif is directed is kinda... Unimportant.
        graph_matcher = find_motifs_iter

        if motif.ignore_direction or not self.graph.is_directed:
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
                if self.graph.has_edge(mapping[u], mapping[v]):
                    return False
            return True

        graph_matches = graph_matcher(only_positive_edges_motif, self.graph)

        results = []
        for r in graph_matches:
            if _doesnt_have_any_of_motifs_negative_edges(r) and (
                self._validate_edge_constraints(
                    r, self.graph, motif.list_edge_constraints()
                )
                and self._validate_node_constraints(
                    r, self.graph, motif.list_node_constraints()
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


class GrandIsoExecutor(NetworkXExecutor):
    def find(self, motif, limit: int = None):
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif)

        """
        # We need to first remove "negative" nodes from the motif, and then
        # filter them out later on. Though this reduces the speed of the graph-
        # matching, NetworkX does not seem to support this out of the box.

        if motif.ignore_direction or not self.graph.is_directed:
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
                if self.graph.has_edge(mapping[u], mapping[v]):
                    return False
            return True

        constraints = motif.list_node_constraints()

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
        )

        results = []
        for r in graph_matches:
            if _doesnt_have_any_of_motifs_negative_edges(r) and (
                self._validate_edge_constraints(
                    r, self.graph, motif.list_edge_constraints()
                )
                # and self._validate_node_constraints(
                #     r, self.graph, motif.list_node_constraints()
                # )
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
