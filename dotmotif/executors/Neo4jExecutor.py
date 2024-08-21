"""
Copyright 2024 The Johns Hopkins University Applied Physics Laboratory.

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

from itertools import product

try:
    from py2neo import Graph
except ImportError:
    raise ImportError(
        "The Neo4jExecutor requires the `py2neo` package. "
        "You can use `dotmotif[neo4j] or install it with `pip install py2neo`."
    )

# Types only:
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .. import dotmotif

from .Executor import Executor


def _remapped_operator(op):
    return {
        "=": "=",
        "==": "=",
        ">=": ">=",
        "<=": "<=",
        "<": "<",
        ">": ">",
        "!=": "<>",
        "<>": "<>",
        "in": "IN",
        "contains": "CONTAINS",
        "!in": "IN",
        "!contains": "CONTAINS",
    }[op]


def _operator_negation_infix(op):
    return {
        "=": False,
        "==": False,
        ">=": False,
        "<=": False,
        "<": False,
        ">": False,
        "!=": False,
        "<>": False,
        "in": False,
        "contains": False,
        "!in": True,
        "!contains": True,
    }[op]


def _quoted_if_necessary(val: str) -> str:
    """
    If the value is already quoted, return it.

    If it has single quotes in it, nest it in double quotes.
    If it has double quotes in it, nest it in single quotes.
    If it has both, nest it in double quotes and escape the double quotes in
    the existing text (i.e., [foo"bar] becomes ["foo\"bar"])
    """
    if val.startswith('"') and val.endswith('"'):
        return val
    elif val.startswith("'") and val.endswith("'"):
        return val
    elif '"' in val and "'" in val:
        return '"' + val.replace('"', '\\"') + '"'
    elif '"' in val:
        return "'" + val + "'"
    elif "'" in val:
        return '"' + val + '"'
    else:
        return '"' + val + '"'


_LOOKUP = {
    "INHIBITS": "INH",
    "EXCITES": "EXC",
    "SYNAPSES": "SYN",
    "INH": "INH",
    "EXC": "EXC",
    "SYN": "SYN",
    "DEFAULT": "SYN",
}

_DEFAULT_ENTITY_LABELS = {
    "node": "Neuron",
    "edge": _LOOKUP,
}


class Neo4jExecutor(Executor):
    """
    A Neo4j executor that runs Cypher queries against a running Neo4j database.

    If you have edit/admin privileges on the database, you can create
    indices on the nodes by calling `create_index` with the attribute name.
    Note that it is not a good idea to let your query executor log in with an
    account that has write access to the database in a production environment.

    """

    def __init__(self, **kwargs) -> None:
        """
        Create a new executor.

        Pass in authentication for a Neo4j database (username/pass) along with
        a db_bolt_uri to connect to an existing database. Alternatively, pass
        a py2neo.Graph object that has already been authenticated.

        Optionally, you can pass in `entity_labels` that specify the names of
        the node and edge labels to use in the database. You must pass in a
        dictionary with the keys "node" and "edge", mapping entity types to
        labels. For an example, see `_DEFAULT_ENTITY_LABELS` in
        `Neo4jExecutor.py`, and for an example of how to make this compatible
        with, say, NeuPrint, see the modified `_DEFAULT_ENTITY_LABELS` used in
        the `NeuPrintExecutor.py` file.

        Arguments:
            db_bolt_uri (str): If connecting to an existing server, the URI
                of the server (including the port, probably 7474).
            username (str: "neo4j"): The username to use to attach to an
                existing server.
            password (str): The password to use to attach to an existing server.
            entity_labels (dict: _DEFAULT_ENTITY_LABELS): The set of labels to
                expect for nodes and edges.

        """
        db_bolt_uri: str = kwargs.get("db_bolt_uri", None)
        username: str = kwargs.get("username", "neo4j")
        password: Optional[str] = kwargs.get("password", None)
        graph: Graph = kwargs.get("graph", None)
        self._entity_labels = kwargs.get("entity_labels", _DEFAULT_ENTITY_LABELS)

        if db_bolt_uri and username and password:
            # Authentication information was provided. Use this to log in and
            # connect to the existing database.
            self._connect_to_existing_graph(db_bolt_uri, username, password)
        elif graph and isinstance(graph, Graph):
            self.G = graph
        else:
            raise ValueError(
                "You must provide either (db_bolt_uri and username and password) "
                "or `graph` (a py2neo.Graph object)."
            )

    def _connect_to_existing_graph(
        self, db_bolt_uri: str, username: str, password: str
    ) -> None:
        try:
            self.G = Graph(db_bolt_uri, username=username, password=password)
        except Exception as e:
            raise ValueError(f"Could not connect to graph {db_bolt_uri}.") from e

    def create_index(self, attribute_name: str):
        """
        Create a new index on the given node attribute.

        Note that edge attributes are NOT supported.
        """
        self.run(
            f"""
        CREATE INDEX index_name IF NOT EXISTS FOR (n:{self._entity_labels["node"]})
        ON (n.{attribute_name})
        """
        )

    def run(self, cypher: str, cursor=True):
        """
        Run an arbitrary cypher command.

        You should usually ignore this, and use .find() instead.

        Arguments:
            cypher (str): The command to run

        Returns:
            The result of the cypher query (py2neo.Table)

        """
        if not cursor:
            return self.G.run(cypher).to_table()
        return self.G.run(cypher)

    def count(self, motif: "dotmotif.Motif", limit=None) -> int:
        """
        Count a motif in a larger graph.

        Arguments:
            motif (dotmotif.Motif)

        """
        qry = self.motif_to_cypher(
            motif, count_only=True, static_entity_labels=self._entity_labels
        )
        if limit:
            qry += f" LIMIT {limit}"
        return int(self.G.run(qry).to_ndarray())

    def find(self, motif: "dotmotif.Motif", limit=None, cursor=True):
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.Motif)

        """
        qry = self.motif_to_cypher(motif, static_entity_labels=self._entity_labels)
        if limit:
            qry += f" LIMIT {limit}"
        if not cursor:
            return self.G.run(qry).to_table()
        return self.G.run(qry)

    @staticmethod
    def motif_to_cypher(
        motif: "dotmotif.Motif",
        count_only: bool = False,
        static_entity_labels: dict = None,
    ) -> str:
        """
        Output a query suitable for Cypher-compatible engines (e.g. Neo4j).

        Returns:
            str: A Cypher query

        """
        static_entity_labels = static_entity_labels or _DEFAULT_ENTITY_LABELS
        # Edges and negative edges
        es = []
        es_neg = []

        motif_graph = motif.to_nx()

        # ID that is assigned to it so that it can hold constraints later on.
        edge_mapping = {}

        for u, v, a in motif_graph.edges(data=True):
            action = static_entity_labels["edge"][
                a.get("action", static_entity_labels["edge"]["DEFAULT"])
            ]
            edge_id = "{}_{}".format(u, v)
            edge_mapping[(u, v)] = edge_id
            if a["exists"]:
                es.append(
                    (
                        "MATCH ({}"
                        + (
                            (":" + static_entity_labels["node"])
                            if static_entity_labels["node"]
                            else ""
                        )
                        + ")-[{}{}]-{}({}"
                        + (
                            (":" + static_entity_labels["node"])
                            if static_entity_labels["node"]
                            else ""
                        )
                        + ")"
                    ).format(
                        u,
                        edge_id,
                        ((":" + action) if action else ""),
                        "" if motif.ignore_direction else ">",
                        v,
                    )
                )
            else:
                es_neg.append(
                    (
                        "NOT ({}"
                        + (
                            (":" + static_entity_labels["node"])
                            if static_entity_labels["node"]
                            else ""
                        )
                        + ")-[:{}]-{}({}"
                        + (
                            (":" + static_entity_labels["node"])
                            if static_entity_labels["node"]
                            else ""
                        )
                        + ")"
                    ).format(u, action, "" if motif.ignore_direction else ">", v)
                )

        delim = "\n" if motif.pretty_print else " "

        conditions = []
        if es_neg:
            conditions = es_neg  # f"{delim} AND ".join(es_neg)

        q_match = delim.join([delim.join(es)])

        # Edge constraints:
        cypher_edge_constraints = []
        for (u, v), a in motif.list_edge_constraints().items():
            for key, constraints in a.items():
                for operator, values in constraints.items():
                    for value in values:
                        cypher_edge_constraints.append(
                            (
                                "NOT ({}[{}] {} {})"
                                if _operator_negation_infix(operator)
                                else "{}[{}] {} {}"
                            ).format(
                                edge_mapping[(u, v)],
                                _quoted_if_necessary(key),
                                _remapped_operator(operator),
                                f'"{value}"' if isinstance(value, str) else value,
                            )
                        )

        # Node constraints:
        cypher_node_constraints = []
        for n, a in motif.list_node_constraints().items():
            for key, constraints in a.items():
                for operator, values in constraints.items():
                    for value in values:
                        cypher_node_constraints.append(
                            (
                                "NOT ({}[{}] {} {})"
                                if _operator_negation_infix(operator)
                                else "{}[{}] {} {}"
                            ).format(
                                n,
                                _quoted_if_necessary(key),
                                _remapped_operator(operator),
                                f'"{value}"' if isinstance(value, str) else value,
                            )
                        )

        # Dynamic node constraints:
        for n, a in motif.list_dynamic_node_constraints().items():
            for key, constraints in a.items():
                for operator, values in constraints.items():
                    for value in values:
                        cypher_node_constraints.append(
                            (
                                "NOT ({}[{}] {} {}[{}])"
                                if _operator_negation_infix(operator)
                                else "{}[{}] {} {}[{}]"
                            ).format(
                                n,
                                _quoted_if_necessary(key),
                                _remapped_operator(operator),
                                value[0],
                                _quoted_if_necessary(value[1]),
                            )
                        )

        # Dynamic edge constraints:
        # Constraints are of the form:
        # {('A', 'B'): {'weight': {'==': ['A', 'C', 'weight']}}}
        for (u, v), constraints in motif.list_dynamic_edge_constraints().items():
            for this_attr, ops in constraints.items():
                for op, (that_u, that_v, that_attr) in ops.items():
                    this_edge_name = edge_mapping[(u, v)]
                    that_edge_name = edge_mapping[(that_u, that_v)]
                    cypher_edge_constraints.append(
                        (
                            "NOT ({}[{}] {} {}[{}])"
                            if _operator_negation_infix(op)
                            else "{}[{}] {} {}[{}]"
                        ).format(
                            this_edge_name,
                            _quoted_if_necessary(this_attr),
                            _remapped_operator(op),
                            that_edge_name,
                            _quoted_if_necessary(that_attr),
                        )
                    )

        conditions.extend([*cypher_node_constraints, *cypher_edge_constraints])

        if count_only:
            q_return = (
                "WITH DISTINCT "
                + ",".join(list(motif_graph.nodes()))
                + " AS __DOTMOTIF_DISTINCT "
                + delim
                + "RETURN COUNT(*)"
            )
        else:
            q_return = "RETURN DISTINCT " + ",".join(list(motif_graph.nodes()))

        if motif.limit:
            q_limit = " LIMIT {}".format(motif.limit)
        else:
            q_limit = ""

        if motif.enforce_inequality:
            _nodes = [str(a) for a in motif_graph.nodes()]
            conditions.extend(
                sorted(
                    list(
                        {
                            "<>".join(sorted(a))
                            for a in list(product(_nodes, _nodes))
                            if a[0] != a[1]
                        }
                    )
                )
            )

        automs = motif.list_automorphisms()
        conditions.extend(["id({}) < id({})".format(a, b) for a, b in automs])

        query = [q_match]
        if conditions:
            query.append("WHERE " + " AND ".join(conditions))
        query.append(q_return)
        if q_limit:
            query.append(q_limit)
        return "{}".format(delim.join(query))
