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

__version__ = "0.2.0"


class MotifError(ValueError):
    pass


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
        ">": "EXCITES",
        "~": "INHIBITS",
        "|": "INHIBITS",
        "+": "EXCITES",
        "?": "SYNAPSES",
        "-": "SYNAPSES",
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
        self.validate = kwargs.get("validate", True)
        self.limit = kwargs.get("limit", None)
        self.enforce_inequality = kwargs.get("enforce_inequality", False)
        self.pretty_print = kwargs.get("pretty_print", True)
        self._g = nx.MultiDiGraph()

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

    def from_csv(self, csv: str, negative_csv: str = "", action="SYNAPSES"):
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
            self._parse_csv_line(line, action=action)

        self.neg_csv = negative_csv
        for line in self.neg_csv.split('\n'):
            self._parse_csv_line(line, exists=False, action=action)

        return self

    def _add_edge(self, u, v, exists=True, action="SYNAPSES"):
        if self.validate:
            candidate_edges = self._g.get_edge_data(u, v, None)
            if candidate_edges:
                for _, e in candidate_edges.items():
                    print(e)
                    if e['exists'] != exists:
                        raise MotifError(
                            "Error adding <{}-{} exists={}, action={}>, {} already exists.".format(
                                u, v, exists, action, e
                            )
                        )
        self._g.add_edge(
            u, v,
            exists=exists,
            action=action
        )


    def _parse_csv_line(self, line: str, exists=True, action="SYNAPSES"):
        # Check that the action is valid
        if action not in self.ACTIONS:
            _reverse_actions = { v: k for k, v in self.ACTIONS.items() }
            if action not in _reverse_actions:
                raise ValueError(
                    "Invalid action. Options: {}".format(self.ACTIONS.keys())
                )
            else:
                action = _reverse_actions[action]

        # Tokenize:
        if len(line) is 0 or line[0] == "#":
            return None
        tokens = line.split(",")
        if len(tokens) != 2:
            raise ValueError(
                "Must be of the form 'pre,post', but got {}".format(line))

        self._add_edge(
            tokens[0], tokens[1],
            exists=exists,
            action=self.ACTIONS[action]
        )

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
        edge_exists = (action[0] != "!")

        self._add_edge(
            u, v,
            action=self.ACTIONS[action[-1]],
            exists=edge_exists
        )

    def to_cypher(self) -> str:
        """
        Output a query suitable for Cypher-compatible engines (e.g. Neo4j).

        Returns:
            str: A Cypher query

        """
        es = []
        es_neg = []
        for u, v, a in self._g.edges(data=True):
            action = self._LOOKUP[a['action']]
            if a['exists']:
                es.append(
                    "MATCH ({}:Neuron)-[:{}]-{}({}:Neuron)".format(
                        u, action,
                        "" if self.ignore_direction else ">",
                        v
                    )
                )
            else:
                es_neg.append(
                    "WHERE NOT ({}:Neuron)-[:{}]-{}({}:Neuron)".format(
                        u, action,
                        "" if self.ignore_direction else ">",
                        v
                    )
                )

        delim = "\n" if self.pretty_print else " "

        q_match = delim.join([delim.join(es), delim.join(es_neg)])
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
            return "{}".format(delim.join([q_match, q_return, q_limit]))

        return "{}".format(delim.join([q_match, q_not_eqs, q_return, q_limit]))

    def to_nx(self) -> nx.DiGraph:
        """
        Output a networkx graph describing the motif.

        Returns:
            networkx.DiGraph

        """
        return self._g
