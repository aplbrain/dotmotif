#!/usr/bin/env python3
from typing import List
import warnings

import networkx as nx

from .. import Parser
from ...validators import Validator


class ParserDMv1(Parser):
    """
    Version 1 of the DotMotif DSL parser.

    Deprecated as of 0.4.3 (Sept 2019).
    """

    _LOOKUP = {"INHIBITS": "INH", "EXCITES": "EXC", "SYNAPSES": "SYN"}

    ACTIONS = {
        ">": "SYNAPSES",
        "~": "INHIBITS",
        "|": "INHIBITS",
        "+": "EXCITES",
        "?": "SYNAPSES",
        "-": "SYNAPSES",
    }

    def __init__(self, validators: List[Validator]) -> None:
        """
        Create a new Parser using the V1 service.

        Now deprecated.
        """
        warnings.warn(
            "Version 1 of the DotMotif DSL parser is deprecated as of v0.4.3. "
            "Please update your code to use `dotmotif.parsers.v2.ParserV2`, "
            "or you can point to `dotmotif.DEFAULT_MOTIF_PARSER` "
            "(which will always point to the latest DSL parser available.)",
            DeprecationWarning,
        )
        self.validators = validators

    def parse(self, dm: str) -> nx.MultiDiGraph:
        """
        Parse the DotMotif using the old V1 DSL parser.

        Now deprecated.
        """
        G = nx.MultiDiGraph()
        for line in dm.split("\n"):
            res = self._parse_dm_line(line.strip())
            if res:
                u, v, action, exists = res
                for val in self.validators:
                    val.validate(G, u, v, action, exists)
                G.add_edge(u, v, exists=exists, action=action)
        return G

    def _parse_dm_line(self, _line: str):
        _line = _line.strip()
        # Tokenize:
        if len(_line) and _line.startswith("#"):
            return None
        line = [t for t in _line.split() if len(t)]
        if len(line) == 0:
            return None

        # Format should be [NEURON_ID, ACTION, NEURON_ID]
        try:
            u, action, v = line
        except ValueError:
            raise ValueError(
                "Line must be of the form [NEURON_ID, ACTION, NEURON_ID], but got {}.".format(
                    line
                )
            )
        edge_exists = action[0] != "!"

        return (u, v, self.ACTIONS[action[-1]], edge_exists)
