#!/usr/bin/env python3
"""
Copyright 2022-2026 The Johns Hopkins Applied Physics Laboratory.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from typing import List, Optional, Union, IO
import copy
import os
import pickle
import warnings
from dotmotif.utils import _deep_merge_constraint_dicts

import networkx as nx
from networkx.algorithms import isomorphism

from .parsers.v2 import ParserV2
from .validators import (
    DisagreeingEdgesValidator,
    ImpossibleConstraintValidator,
    Validator,
)

from .executors.NetworkXExecutor import NetworkXExecutor
from .executors.GrandIsoExecutor import GrandIsoExecutor

__version__ = "0.18.0"

DEFAULT_MOTIF_PARSER = ParserV2


class MotifError(ValueError):
    pass


class Motif:
    """
    Container class for dotmotif operations.

    See __init__ documentation for more details.
    """

    def __init__(self, input_motif: Optional[str] = None, **kwargs):
        """
        Create a new dotmotif object.

        Arguments:
            input_motif (str: None): Optionally, a DotMotif DSL defined motif,
                or a path to a .motif file that contains a motif.
            ignore_direction (bool: False): Whether to disregard direction when
                generating the database query
            limit (int: None): A limit (if any) to impose on the query results
            enforce_inequality (bool: False): Whether to enforce inequality; in
                other words, whether two nodes should be permitted to be aliases
                for the same node. For example, A>B>C; if A!=C, then set to True
            pretty_print (bool: True)
            parser (dotmotif.parsers.Parser: DEFAULT_MOTIF_PARSER): The parser
                to use to parse the document. Defaults to the v2 parser.
            exclude_automorphisms (bool: False): Whether to exclude automorphism
                variants of the motif when returning results.
            validators (List[Validator]): A list of dotmotif.Validators to use
                when verifying the motif for correctness and executability.

        """
        self.ignore_direction = kwargs.get("ignore_direction", False)
        self.limit = kwargs.get("limit", None)
        self.enforce_inequality = kwargs.get("enforce_inequality", False)
        self.pretty_print = kwargs.get("pretty_print", True)
        self.parser = kwargs.get("parser", DEFAULT_MOTIF_PARSER)
        self.exclude_automorphisms = kwargs.get("exclude_automorphisms", False)
        self.validators: List[Validator] = kwargs.get(
            "validators",
            [DisagreeingEdgesValidator(), ImpossibleConstraintValidator()],
        )
        self._g = nx.MultiDiGraph()

        self._edge_constraints = {}
        self._node_constraints = {}
        self._dynamic_edge_constraints = {}
        self._dynamic_node_constraints = {}
        self._automorphisms = []

        if input_motif:
            self.from_motif(input_motif)

    def from_motif(self, cmd: str):
        """
        Ingest a dotmotif-format string.

        Arguments:
            cmd (str): A string in dotmotif form, or a .dm filename on disk

        Returns:
            A pointer to this dotmotif object, for chaining

        """
        if len(cmd.split("\n")) == 1:
            try:
                cmd = open(cmd, "r").read()
            except FileNotFoundError:
                pass

        result = self.parser(validators=self.validators).parse(cmd)
        (
            self._g,
            self._edge_constraints,
            self._node_constraints,
            self._dynamic_edge_constraints,
            self._dynamic_node_constraints,
            self._automorphisms,
        ) = result

        self._propagate_automorphic_constraints()

        # Post-parse validation hooks (e.g., constraint collisions from automorphisms)
        for val in self.validators:
            if hasattr(val, "validate_motif"):
                val.validate_motif(self)

        return self

    def from_nx(self, graph: nx.DiGraph) -> "Motif":
        """
        Ingest directly from a graph.

        Arguments:
            graph (nx.DiGraph): The graph to import

        Returns:
            None

        """

        warnings.warn(
            "The dotmotif#from_nx call is deprecated as of v0.4.3. "
            "For more information, please read here: "
            "https://github.com/aplbrain/dotmotif/issues/43",
            DeprecationWarning,
        )
        self._g = copy.deepcopy(graph)
        self._edge_constraints = {}
        self._node_constraints = {}
        self._dynamic_edge_constraints = {}
        self._dynamic_node_constraints = {}
        self._automorphisms = []
        for _, _, edge_attrs in self._g.edges(data=True):
            edge_attrs.setdefault("exists", True)
            edge_attrs.setdefault("action", "SYN")
        return self

    def to_nx(self) -> nx.DiGraph:
        """
        Output a networkx graph describing the motif.

        Returns:
            networkx.DiGraph

        """
        return self._g

    def list_edge_constraints(self):
        return self._edge_constraints

    def list_dynamic_edge_constraints(self):
        return self._dynamic_edge_constraints

    def list_node_constraints(self):
        return self._node_constraints

    def list_dynamic_node_constraints(self):
        return self._dynamic_node_constraints

    def list_automorphisms(self):
        """
        List ordering constraints that pick one match per automorphism class.

        Each entry is a pair (a, b) meaning the host node matched to `a` must
        sort before the host node matched to `b`.

        When `exclude_automorphisms` is False, this returns only the pairs
        that were declared explicitly with `===`.

        """
        if not self.exclude_automorphisms:
            return self._automorphisms
        return _symmetry_breaking_pairs(self._automorphism_group())

    def _automorphism_group(self) -> List[dict]:
        """
        Every node permutation that maps the motif onto itself.

        A permutation counts only if it preserves edge existence, edge
        action, static and dynamic edge constraints, and static and dynamic
        node constraints, not just the bare edge structure.

        """
        g = self.to_nx()
        # Choose the appropriate VF2 matcher depending on directedness
        # and whether the graph is a multigraph.
        if g.is_directed():
            if g.is_multigraph():
                matcher_cls = isomorphism.MultiDiGraphMatcher
            else:
                matcher_cls = isomorphism.DiGraphMatcher
        else:
            if g.is_multigraph():
                matcher_cls = isomorphism.MultiGraphMatcher
            else:
                matcher_cls = isomorphism.GraphMatcher

        edge_match = _multiedge_match if g.is_multigraph() else _edge_match
        matcher = matcher_cls(g, g, edge_match=edge_match)

        node_constraints = self._node_constraints
        dyn_node = _canonical(self._dynamic_node_constraints)
        dyn_edge = _canonical(self._dynamic_edge_constraints)

        group = []
        for perm in matcher.isomorphisms_iter():
            if any(
                _canonical(node_constraints.get(n, {}))
                != _canonical(node_constraints.get(perm[n], {}))
                for n in g.nodes
            ):
                continue
            if (
                _canonical(
                    _permute_dynamic_node_constraints(
                        self._dynamic_node_constraints, perm
                    )
                )
                != dyn_node
            ):
                continue
            if (
                _canonical(
                    _permute_dynamic_edge_constraints(
                        self._dynamic_edge_constraints, perm
                    )
                )
                != dyn_edge
            ):
                continue
            group.append(perm)
        return group

    def _propagate_automorphic_constraints(self):
        """
        Take constraints on automorphic nodes and add them to symmetric nodes.

        """
        # Loop over automorphisms that have been explicitly defined (in the
        # dotmotif DSL, this is done with the triple-equality === operator.)
        # Note to future self: We DON'T loop over implicit automorphisms because
        # there is no guarantee that the user intends for structural symmetries
        # to also be symmetries in the constraint space.
        for u, v in self._automorphisms:
            # Add a superset of constraints on the two nodes.
            # First add attributes on the nodes themselves:
            constraints = _deep_merge_constraint_dicts(
                self._node_constraints.get(u, {}),
                self._node_constraints.get(v, {}),
            )
            self._node_constraints[u] = constraints
            self._node_constraints[v] = constraints

    def save(self, fname: Union[str, IO[bytes]]) -> Union[str, IO[bytes]]:
        """
        Save the motif to a file on disk.

        Arguments:
            fname (str): A path on disk for IO

        Returns:
            Pointer to File-like.

        """
        if isinstance(fname, (str, os.PathLike)):
            with open(fname, "wb") as f:
                pickle.dump(self, f)
        else:
            pickle.dump(self, fname)
        return fname

    @staticmethod
    def load(fname: Union[str, IO[bytes]]) -> "Motif":
        """
        Load the motif from a file on disk.

        Arguments:
            fname (str): A path on disk for IO

        Returns:
            Pointer to File-like.

        """
        if isinstance(fname, (str, os.PathLike)):
            with open(fname, "rb") as f:
                return pickle.load(f)
        else:
            return pickle.load(fname)


__all__ = ["Motif", "MotifError", "NetworkXExecutor", "GrandIsoExecutor"]


def _canonical(obj):
    """A hashable, order-independent form of a nested constraint structure."""
    if isinstance(obj, dict):
        return tuple(sorted((repr(k), _canonical(v)) for k, v in obj.items()))
    if isinstance(obj, (list, tuple, set)):
        return tuple(sorted(repr(_canonical(v)) for v in obj))
    return repr(obj)


def _edge_signature(attrs: dict):
    return (
        attrs.get("exists", True),
        attrs.get("action", "SYN"),
        _canonical(attrs.get("constraints", {})),
    )


def _edge_match(e1: dict, e2: dict) -> bool:
    return _edge_signature(e1) == _edge_signature(e2)


def _multiedge_match(e1: dict, e2: dict) -> bool:
    return sorted(map(repr, map(_edge_signature, e1.values()))) == sorted(
        map(repr, map(_edge_signature, e2.values()))
    )


def _permute_dynamic_node_constraints(constraints: dict, perm: dict) -> dict:
    out: dict = {}
    for node, attrs in constraints.items():
        for attr, ops in attrs.items():
            for op, values in ops.items():
                out.setdefault(perm[node], {}).setdefault(attr, {}).setdefault(
                    op, []
                ).extend((perm[other], other_attr) for other, other_attr in values)
    return out


def _permute_dynamic_edge_constraints(constraints: dict, perm: dict) -> dict:
    out: dict = {}
    for (u, v), attrs in constraints.items():
        for attr, ops in attrs.items():
            for op, values in ops.items():
                out.setdefault((perm[u], perm[v]), {}).setdefault(attr, {}).setdefault(
                    op, []
                ).extend(
                    (perm[ou], perm[ov], other_attr) for ou, ov, other_attr in values
                )
    return out


def _symmetry_breaking_pairs(group: List[dict]) -> List[tuple]:
    """
    Ordering constraints that keep exactly one match per automorphism class.

    Follows Grochow and Kellis (2007): pick the node with the largest orbit,
    require it to sort before every other node in that orbit, then repeat on
    the subgroup that fixes it. Pairwise constraints drawn from every
    automorphism at once (the previous approach) only work when the group is
    made of independent swaps; for a rotation, such as a directed 3-cycle,
    they drop valid matches.

    """
    pairs = []
    while len(group) > 1:
        nodes = sorted(group[0].keys(), key=repr)
        orbits = {n: {perm[n] for perm in group} for n in nodes}
        base = max(nodes, key=lambda n: len(orbits[n]))
        for other in sorted(orbits[base] - {base}, key=repr):
            pairs.append((base, other))
        group = [perm for perm in group if perm[base] == base]
    return pairs
