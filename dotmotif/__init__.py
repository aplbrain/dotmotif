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

from itertools import product

import networkx as nx


class dotmotif:
    """
    Container class for dotmotif operations.

    See __init__ documentation for more details.
    """

    _LOOKUP = {
        "INHIBITS": "INH",
        "EXCITES":  "EXC",
        "SYNAPSES": "SYN",
    }

    ACTIONS = {
        "-~": "INHIBITS",
        "-+": "EXCITES",
        "-?": "SYNAPSES",
    }

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
        self._g = nx.DiGraph()

    def from_motif(self, cmd: str):
        """
        Ingest a dotmotif-format string.

        Arguments:
            cmd (str): A string in dotmotif form, or a .dm filename on disk

        Returns:
            A pointer to this dotmotif object, for chaining

        """
        if len(cmd.split("\n")) is 1:
            cmd = open(cmd, 'r').read()

        self.cmd = cmd
        for line in self.cmd.split('\n'):
            self._parse_dm_line(line.strip(";"))
        return self

    def from_csv(self, csv: str):
        """
        Ingest a CSV-format string.

        Arguments:
            cmd (str): A string in CSV form, or a .csv filename on disk

        Returns:
            A pointer to this dotmotif object, for chaining

        """
        if len(csv.split("\n")) is 1:
            csv = open(csv, 'r').read()

        self.csv = csv
        for line in self.csv.split('\n'):
            self._parse_csv_line(line)
        return self

    def _parse_csv_line(self, line: str):
        # Tokenize:
        if len(line) is 0 or line[0] == "#":
            return None
        tokens = line.split(",")
        if len(tokens) != 2:
            raise ValueError(
                "Must be of the form 'pre,post', but got {}".format(line))
        self._g.add_edge(tokens[0], tokens[1])

    def _parse_dm_line(self, line: str):
        # Tokenize:
        if len(line.strip()) and line.strip()[0] == "#":
            return None
        line = [t for t in line.split() if len(t)]
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
        self._g.add_edge(u, v, action=action)

    def to_cypher(self) -> str:
        """
        Output a query suitable for Cypher-compatible engines (e.g. Neo4j).

        Returns:
            str: A Cypher query

        """
        es = []
        for u, v, a in self._g.edges(data=True):
            if self.ignore_direction:
                es.append(
                    "MATCH (" + u + ":Neuron)-[:SYN]-(" + v + ":Neuron)"
                )
            else:
                es.append(
                    "MATCH (" + u + ":Neuron)-[:SYN]->(" + v + ":Neuron)"
                )

        q_match = "{}".format(" ".join(es))
        q_return = "RETURN " + ",".join(list(self._g.nodes()))

        if self.limit:
            q_limit = " LIMIT {}".format(self.limit)
        else:
            q_limit = ""

        if self.enforce_inequality:
            q_not_eqs = "WHERE " + " AND ".join(set([
                "<>".join(sorted(a))
                for a in list(product(self._g.nodes(), self._g.nodes()))
                if a[0] != a[1]
            ]))
        else:
            q_not_eqs = ""

        return "{} {} {} {}".format(q_match, q_not_eqs, q_return, q_limit)

    def to_nx(self) -> nx.DiGraph:
        """
        Output a networkx graph describing the motif.

        Returns:
            networkx.DiGraph

        """
        return self._g
