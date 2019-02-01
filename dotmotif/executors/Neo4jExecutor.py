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
import os
import time

import pandas as pd
import networkx as nx
import random
import string

import docker
from py2neo import Graph
import requests

# Types only:
from py2neo.data import Table
import networkx as nx
from .. import dotmotif

from .Executor import Executor
from ..ingest import NetworkXIngester


def _remapped_operator(op):
    return {
        "=": "=",
        "==": "=",
        ">=": ">=",
        "<=": "<=",
        "<": "<",
        ">": ">",
        "!=": "!=",
        "<>": "!=",
    }[op]


class Neo4jExecutor(Executor):
    """
    A Neo4j executor that runs Cypher queries against a running Neo4j database.
    """

    def __init__(self, **kwargs) -> None:
        """
        Create a new executor.

        If there is an already-running Neo4j database, you can pass in
        authentication information and it will connect.

        If there is no existing database, you can pass in a graph to ingest
        and the executor will connect to it automatically.

        If there is no existing database and you do not pass in a graph, you
        must pass an `import_directory`, which the container will mount as an
        importable CSV resource.
        """

        db_bolt_uri: str = kwargs.get("db_bolt_uri", None)
        username: str = kwargs.get("username", "neo4j")
        password: str = kwargs.get("password", None)
        self._max_memory_size: str = kwargs.get("max_memory", "8G")
        self.max_retries: int = kwargs.get("max_retries", 20)
        self._initial_heap_size: str = kwargs.get("initial_memory", "4G")

        graph: nx.Graph = kwargs.get("graph", None)
        import_directory: str = kwargs.get("import_directory", None)

        self._created_container = False

        if db_bolt_uri and password:
            # Authentication information was provided. Use this to log in and
            # connect to the existing database.
            self._connect_to_existing_graph(db_bolt_uri, username, password)

        elif graph:
            export_dir = "export-custom-graph"
            # A networkx graph was provided.
            # We must export this to a set of CSV files, drop them to disk,
            # and then we can use the same strategy as `import_directory` to
            # run a container.
            nxi = NetworkXIngester(graph, export_dir)
            try:
                nxi.ingest()
            except Exception as e:
                raise ValueError(f"Could not export graph: {e}")

            self._create_container(export_dir)

        elif import_directory:
            self._create_container(import_directory)

        else:
            raise ValueError(
                "You must supply either an existing db or a graph to load."
            )

    def __del__(self):
        if self._created_container:
            self._teardown_container()

    def _connect_to_existing_graph(
        self, db_bolt_uri: str, username: str, password: str
    ) -> None:
        try:
            self.G = Graph(db_bolt_uri, username=username, password=password)
        except:
            raise ValueError(f"Could not connect to graph {db_bolt_uri}.")

    def _create_container(self, import_dir: str):
        # Create a docker container:
        self.docker_client = docker.from_env()
        self._running_container = self.docker_client.containers.run(
            "neo4j:3.4",
            command="""
            bash -c './bin/neo4j-admin import --id-type STRING --nodes:Neuron "/import/export-neurons-.*.csv" --relationships:SYN "/import/export-synapses-.*.csv" &&
            ./bin/neo4j-admin set-initial-password neo4jpw &&
            ./bin/neo4j start &&
            tail -f /dev/null'""",
            # auto_remove=True,
            detach=True,
            environment={
                "NEO4J_dbms_memory_heap_initial__size": self._initial_heap_size,
                "NEO4J_dbms_memory_heap_max__size": self._max_memory_size,
            },
            volumes={f"{os.getcwd()}/{import_dir}": {"bind": "/import", "mode": "ro"}},
            ports={7474: 7474, 7687: 7687},
            network_mode="bridge",
        )
        self._created_container = True
        container_is_ready = False
        tries = 0
        while not container_is_ready:
            try:
                res = requests.get("http://localhost:7474")
                if res.status_code == 200:
                    container_is_ready = True
            except:
                pass
            else:
                tries += 1
                time.sleep(2)
                if tries > self.max_retries:
                    raise IOError(
                        f"Could not connect to neo4j container {self._running_container}."
                    )
        self.G = Graph(password="neo4jpw")

    def _teardown_container(self):
        self._running_container.stop()
        self._running_container.remove()

    def run(self, cypher: str, cursor=True) -> Table:
        """
        Run an arbitrary cypher command.

        You should usually ignore this, and use .find() instead.

        Arguments:
            cypher (str): The command to run

        Returns:
            The result of the cypher query

        """
        if not cursor:
            return self.G.run(cypher).to_table()
        return self.G.run(cypher)

    def find(self, motif: dotmotif, limit=None, cursor=True) -> Table:
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif)

        """
        qry = self.motif_to_cypher(motif)
        if limit:
            qry += f" LIMIT {limit}"
        if not cursor:
            return self.G.run(qry).to_table()
        return self.G.run(qry)

    @staticmethod
    def motif_to_cypher(motif: dotmotif) -> str:
        """
        Output a query suitable for Cypher-compatible engines (e.g. Neo4j).

        Returns:
            str: A Cypher query

        """
        # Edges and negative edges
        es = []
        es_neg = []

        motif_graph = motif.to_nx()

        # This will hold the edge mapping of (u, v) in the motif to the random
        # ID that is assigned to it so that it can hold constraints later on.
        edge_mapping = {}

        for u, v, a in motif_graph.edges(data=True):
            action = motif._LOOKUP[a["action"]]
            # edge_id = random_id()
            edge_id = "{}_{}".format(u, v)
            edge_mapping[(u, v)] = edge_id
            if a["exists"]:
                es.append(
                    "MATCH ({}:Neuron)-[{}:{}]-{}({}:Neuron)".format(
                        u, edge_id, action, "" if motif.ignore_direction else ">", v
                    )
                )
            else:
                es_neg.append(
                    "NOT ({}:Neuron)-[{}:{}]-{}({}:Neuron)".format(
                        u, edge_id, action, "" if motif.ignore_direction else ">", v
                    )
                )

        delim = "\n" if motif.pretty_print else " "

        if len(es_neg):
            q_match = delim.join(
                [delim.join(es), "WHERE " + f"{delim} AND ".join(es_neg)]
            )
        else:
            q_match = delim.join([delim.join(es)])

        # Edge constraints:
        cypher_edge_constraints = []
        for (u, v), a in motif.list_edge_constraints().items():
            for key, constraints in a.items():
                for operator, values in constraints.items():
                    for value in values:
                        cypher_edge_constraints.append(
                            "{}.{} {} {}".format(
                                edge_mapping[(u, v)],
                                key,
                                _remapped_operator(operator),
                                f'"{value}"' if isinstance(value, str) else value,
                            )
                        )
        if cypher_edge_constraints:
            q_match += delim + "WHERE " + " AND ".join(cypher_edge_constraints)

        # Edge constraints:
        cypher_node_constraints = []
        for n, a in motif.list_node_constraints().items():
            for key, constraints in a.items():
                for operator, values in constraints.items():
                    for value in values:
                        cypher_node_constraints.append(
                            "{}.{} {} {}".format(
                                n,
                                key,
                                _remapped_operator(operator),
                                f'"{value}"' if isinstance(value, str) else value,
                            )
                        )
        if cypher_node_constraints:
            q_match += delim + "WHERE " + " AND ".join(cypher_node_constraints)

        q_return = "RETURN DISTINCT " + ",".join(list(motif_graph.nodes()))

        if motif.limit:
            q_limit = " LIMIT {}".format(motif.limit)
        else:
            q_limit = ""

        if motif.enforce_inequality:
            q_not_eqs = "WHERE " + " AND ".join(
                set(
                    [
                        "<>".join(sorted(a))
                        for a in list(product(motif_graph.nodes(), motif_graph.nodes()))
                        if a[0] != a[1]
                    ]
                )
            )
        else:
            return "{}".format(delim.join([q_match, q_return, q_limit]))

        return "{}".format(delim.join([q_match, q_not_eqs, q_return, q_limit]))
