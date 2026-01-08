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

__version__ = "0.14.0"

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
        for u, v, edge_attrs in self._g.edges(data=True):
            if "exists" not in edge_attrs:
                self._g.edges[u, v]["exists"] = True
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
        if not self.exclude_automorphisms:
            return self._automorphisms

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

        res = matcher_cls(g, g).subgraph_isomorphisms_iter()
        autos = set()
        for auto in res:
            for k, v in auto.items():
                if k != v:
                    autos.add(tuple(sorted([k, v])))
        return list(autos)

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
        if isinstance(fname, str):
            f = open(fname, "wb")
        else:
            f = fname
        pickle.dump(self, f)
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
        if isinstance(fname, str):
            f = open(fname, "rb")
        else:
            f = fname
        result = pickle.load(f)
        f.close()
        return result


__all__ = ["Motif", "MotifError", "NetworkXExecutor", "GrandIsoExecutor"]
