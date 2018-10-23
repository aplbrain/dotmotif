#!/usr/bin/env python3
from .. import Parser

import networkx as nx

class ParserDMv1(Parser):
    """
    """

    def __init__(self):
        pass

    def parse(self, dm: str) -> nx.DiGraph:
        """
        """
        G = nx.DiGraph()
        for line in dm.split('\n'):
            res = self._parse_dm_line(line.strip())
            if res:
                u, v, exists, action = res
                G.add_edge(u, v, exists=exists, action=action)

    def _parse_dm_line(self, _line: str):
        _line = _line.strip()
        # Tokenize:
        if len(_line) and _line.startswith("#"):
            return None
        line = [t for t in _line.split() if len(t)]
        if len(line) is 0:
            return None

        # Format should be [NEURON_ID, ACTION, NEURON_ID]
        try:
            u, action, v = line
        except ValueError:
            raise ValueError(
                "Line must be of the form [NEURON_ID, ACTION, NEURON_ID], but got {}.".format(
                    line)
            )
        edge_exists = (action[0] != "!")

        return (
            u, v,
            self.ACTIONS[action[-1]],
            edge_exists
        )
