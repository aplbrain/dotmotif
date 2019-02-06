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

import networkx as nx

from .parsers.v2 import ParserV2
from .validators import DisagreeingEdgesValidator

__version__ = "0.4.0"

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

        """
        self.ignore_direction = kwargs.get("ignore_direction", False)
        self.limit = kwargs.get("limit", None)
        self.enforce_inequality = kwargs.get("enforce_inequality", False)
        self.pretty_print = kwargs.get("pretty_print", True)
        self.parser = kwargs.get("parser", DEFAULT_MOTIF_PARSER)
        self.validators = kwargs.get("validators", [DisagreeingEdgesValidator()])
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
            self._g, self._edge_constraints, self._node_constraints = result
        else:
            # For backwards compatibility with parser v1
            self._g = result

        return self

    def from_nx(self, graph: nx.DiGraph) -> None:
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
