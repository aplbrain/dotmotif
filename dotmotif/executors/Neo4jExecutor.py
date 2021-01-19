"""
Copyright 2020 The Johns Hopkins University Applied Physics Laboratory.

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
import os
import time
from uuid import uuid4

from py2neo import Graph
import tamarind

# Types only:
import networkx as nx
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
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
        "!=": "<>",
        "<>": "<>",
        "in": "IN",
        "contains": "CONTAINS",
    }[op]


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

    .
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

        Arguments:
            db_bolt_uri (str): If connecting to an existing server, the URI
                of the server (including the port, probably 7474).
            username (str: "neo4j"): The username to use to attach to an
                existing server.
            password (str): The password to use to attach to an existing server.
            graph (nx.Graph): If provisioning a new database, the networkx
                graph to import into the database.
            import_directory (str): If provisioning a new database, the local
                directory to crawl for CSVs to import into the Neo4j database.
                Commonly used when you want to quickly and easily start a new
                Executor that uses the export from a previous graph.
            autoremove_container (bool: True): Whether to delete the container
                when the executor is deconstructed. Set to False if you'd like
                to be able to connect with other executors after the first one
                has closed.
            max_memory (str: "4G"): The maximum amount of memory to provision.
            initial_memory (str: "2G"): The starting heap-size for the Neo4j
                container's JVM.
            max_retries (int: 20): The number of times DotMotif should try to
                connect to the neo4j container before giving up.
            wait_for_boot (bool: True): Whether the process should pause to
                wait for a provisioned Docker container to come online.
            entity_labels (dict: _DEFAULT_ENTITY_LABELS): The set of labels to
                use for nodes and edges.

        """
        db_bolt_uri: Optional[str] = kwargs.get("db_bolt_uri", None)
        username: str = kwargs.get("username", "neo4j")
        password: Optional[str] = kwargs.get("password", None)
        self._autoremove_container: bool = kwargs.get("autoremove_container", True)
        self._wait_for_boot: bool = kwargs.get("wait_for_boot", True)
        self._max_memory_size: str = kwargs.get("max_memory", "4G")
        self._initial_heap_size: str = kwargs.get("initial_memory", "2G")
        self.max_retries: int = kwargs.get("max_retries", 20)
        self._entity_labels = kwargs.get("entity_labels", _DEFAULT_ENTITY_LABELS)

        graph: nx.Graph = kwargs.get("graph", None)
        import_directory: Optional[str] = kwargs.get("import_directory", None)

        self._created_container = False
        self._tamarind_provisioner = None

        if (
            (db_bolt_uri and graph)
            or (db_bolt_uri and import_directory)
            or (import_directory and graph)
        ):
            raise ValueError(
                "Specify EXACTLY ONE of db_bolt_uri/graph/import_directory."
            )

        if db_bolt_uri:
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

            self._tamarind_provisioner = tamarind.Neo4jDockerProvisioner(
                autoremove_container=self._autoremove_container,
                max_memory_size=self._max_memory_size,
                initial_heap_size=self._initial_heap_size,
            )
            self._create_container(export_dir)

        elif import_directory:
            self._tamarind_provisioner = tamarind.Neo4jDockerProvisioner(
                autoremove_container=self._autoremove_container,
                max_memory_size=self._max_memory_size,
                initial_heap_size=self._initial_heap_size,
            )
            self._create_container(import_directory)

        else:
            raise ValueError(
                "You must supply either an existing db or a graph to load."
            )

    def __del__(self):
        """
        Destroy the docker container from the running processes.

        Also will handle (TODO) other teardown actions.
        """
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
        self._tamarind_container_id = str(uuid4())
        (
            self._running_container,
            self._container_port,
        ) = self._tamarind_provisioner.start(
            self._tamarind_container_id,
            import_path=f"{os.getcwd()}/{import_dir}",
            run_before=f"""./bin/neo4j-admin import --id-type STRING --nodes:{entity_labels['node']} "/import/export-neurons-.*.csv" --relationships:{entity_labels['edge']['DEFAULT']} "/import/export-synapses-.*.csv" """,
            wait=self._wait_for_boot,
        )
        self._created_container = True
        container_is_ready = False
        tries = 0
        while not container_is_ready:
            try:
                self.G = self._tamarind_provisioner[self._tamarind_container_id]
                container_is_ready = True
            except Exception as e:
                tries += 1
                if tries > self.max_retries:
                    raise IOError(
                        f"Could not connect to neo4j container {self._running_container}. "
                        "For more information, see Troubleshooting-Neo4jExecutor.md in docs/."
                    )
                time.sleep(5)
        self.G = self._tamarind_provisioner[self._tamarind_container_id]

    def _teardown_container(self):
        self._tamarind_provisioner.stop(self._tamarind_container_id)

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

    def count(self, motif: "dotmotif", limit=None) -> int:
        """
        Count a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif)

        """
        qry = self.motif_to_cypher(motif, count_only=True)
        if limit:
            qry += f" LIMIT {limit}"
        return int(self.G.run(qry).to_ndarray())

    def find(self, motif: "dotmotif", limit=None, cursor=True):
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
    def motif_to_cypher(
        motif: "dotmotif",
        count_only: bool = False,
        edge_name_lookup: dict = None,
        static_entity_labels: dict = None,
    ) -> str:
        """
        Output a query suitable for Cypher-compatible engines (e.g. Neo4j).

        Returns:
            str: A Cypher query

        """
        edge_name_lookup = edge_name_lookup or _LOOKUP
        static_entity_labels = static_entity_labels or _DEFAULT_ENTITY_LABELS
        # Edges and negative edges
        es = []
        es_neg = []

        motif_graph = motif.to_nx()

        # ID that is assigned to it so that it can hold constraints later on.
        edge_mapping = {}

        for u, v, a in motif_graph.edges(data=True):
            action = edge_name_lookup[
                a.get("action", static_entity_labels["edge"]["DEFAULT"])
            ]
            edge_id = "{}_{}".format(u, v)
            edge_mapping[(u, v)] = edge_id
            if a["exists"]:
                es.append(
                    (
                        "MATCH ({}:"
                        + static_entity_labels["node"]
                        + ")-[{}:{}]-{}({}:"
                        + static_entity_labels["node"]
                        + ")"
                    ).format(
                        u, edge_id, action, "" if motif.ignore_direction else ">", v
                    )
                )
            else:
                es_neg.append(
                    (
                        "NOT ({}:"
                        + static_entity_labels["node"]
                        + ")-[:{}]-{}({}:"
                        + static_entity_labels["node"]
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
                            "{}.{} {} {}".format(
                                edge_mapping[(u, v)],
                                key,
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
                            "{}.{} {} {}".format(
                                n,
                                key,
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
                            "{}.{} {} {}.{}".format(
                                n,
                                key,
                                _remapped_operator(operator),
                                value[0],
                                value[1],
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
