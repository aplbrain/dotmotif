#!/usr/bin/env python3
import abc

import networkx as nx

class Parser(abc.ABC):
    ...

    def parse(self, dm: str) -> nx.DiGraph:
        ...
