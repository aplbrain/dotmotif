#!/usr/bin/env python3
"""
Copyright 2018 The Johns Hopkins University Applied Physics Laboratory.

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

from typing import Union, IO
import pickle

import networkx as nx
from networkx.algorithms import isomorphism

from .parsers.v2 import ParserV2
from .validators import DisagreeingEdgesValidator

from .executors.NetworkXExecutor import NetworkXExecutor

__version__ = "0.4.2"

DEFAULT_MOTIF_PARSER = ParserV2


class MotifError(ValueError):
    pass


class dotmotif:
    """
    Container class for dotmotif operations.

    See __init__ documentation for more details.
    """

    def __init__(self, **kwargs):
        """
        Create a new dotmotif object.

        Arguments:
            ignore_direction (bool: False): Whether to disregard direction when
                generating the database query
            limit (int: None): A limit (if any) to impose on the query results
            enforce_inequality (bool: False): Whether to enforce inequality; in
                other words, whether two nodes should be permitted to be aliases
                for the same node. For example, A>B>C; if A!=C, then set to True
            pretty_print (bool: True): Whether the motif should be pretty-
                printed. This option is irrelevant unless you're debugging your
                queries and want to read, e.g., cypher directly.
            parser (dotmotif.parsers.Parser: DEFAULT_MOTIF_PARSER): Which parser
                to use to parse the motif-syntax input. Defaults to the latest
                available parser. Don't change this unless you're having back-
                wards-compatibility issues.
            exclude_automorphisms (bool: False): Whether to automatically ignore
                automorphisms when returning results. If set to True, this will
                only return ONE representative out of an automorphism group,
                selected arbitrarily. If set to False, this will return ALL
                results, at the expense of a much larger result set.
            validators (List[dotmotif.validators.Validator]): The list of vali-
                dators to use to verify the motif. You can pass an empty array
                if you'd like no validation to be run prior to query execution.

        """
        self.ignore_direction = kwargs.get("ignore_direction", False)
        self.limit = kwargs.get("limit", None)
        self.enforce_inequality = kwargs.get("enforce_inequality", False)
        self.pretty_print = kwargs.get("pretty_print", True)
        self.parser = kwargs.get("parser", DEFAULT_MOTIF_PARSER)
        self.exclude_automorphisms = kwargs.get("exclude_automorphisms", False)
        self.validators = kwargs.get(
            "validators", [DisagreeingEdgesValidator()]
        )
        self._LOOKUP = {
            "INHIBITS": "INH",
            "EXCITES": "EXC",
            "SYNAPSES": "SYN",
            "INH": "INH",
            "EXC": "EXC",
            "SYN": "SYN",
        }
        self._g = nx.MultiDiGraph()

        self._edge_constraints = {}
        self._node_constraints = {}
        self._automorphisms = []

    def from_motif(self, cmd: str):
        """
        Ingest a dotmotif-format string.

        Arguments:
            cmd (str): A string in dotmotif form, or a .dm filename on disk

        Returns:
            A pointer to this dotmotif object, for chaining

        """
        if len(cmd.split("\n")) is 1:
            try:
                cmd = open(cmd, "r").read()
            except FileNotFoundError:
                pass

        result = self.parser(validators=self.validators).parse(cmd)
        if isinstance(result, tuple):
            self._g, self._edge_constraints, self._node_constraints, self._automorphisms = (
                result
            )
        else:
            # For backwards compatibility with parser v1
            self._g = result

        return self

    def from_nx(self, graph: nx.DiGraph) -> 'dotmotif':
        """
        Ingest directly from a graph.

        Arguments:
            graph (nx.DiGraph): The graph to import

        Returns:
            None

        """
        self._g = graph
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

    def list_node_constraints(self):
        return self._node_constraints

    def list_automorphisms(self):
        if not self.exclude_automorphisms:
            return self._automorphisms

        g = self.to_nx()
        res = isomorphism.GraphMatcher(g, g).subgraph_isomorphisms_iter()
        autos = set()
        for auto in res:
            for k, v in auto.items():
                if k != v:
                    autos.add(tuple(sorted([k, v])))
        return list(autos)

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
    def load(fname: Union[str, IO[bytes]]) -> "dotmotif":
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
        return pickle.load(f)
