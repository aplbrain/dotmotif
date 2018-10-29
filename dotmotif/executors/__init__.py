# Standard imports
from itertools import product
import os
import time


# Non-standard Imports
import docker
import pandas as pd
from py2neo import Database, Graph
import requests

# Types only:
from py2neo.data import Table
import networkx as nx

# default Ingester
from ..ingest import NetworkXIngester
from .. import dotmotif


class Executor:
    ...

    def find(self, motif: dotmotif, limit: int=None):
        ...


class NetworkXExecutor(Executor):
    """
    A query executor that runs inside RAM.

    Uses NetworkX's built-in (VF2) subgraph isomorphism algo. Good for very
    small graphs, since this won't scale particularly well.
    """

    def __init__(self, **kwargs) -> None:
        """
        Create a new NetworkXExecutor.

        Arguments:
            graph (networkx.Graph)

        Returns:
            None

        """
        if 'graph' in kwargs:
            self.graph = kwargs.get('graph')
        else:
            raise ValueError(
                "You must pass a graph to the NetworkXExecutor constructor."
            )

    def find(self, motif, limit: int=None):
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif)

        """
        gm = nx.algorithms.isomorphism.GraphMatcher(self.graph, motif.to_nx())
        res = gm.subgraph_isomorphisms_iter()
        return pd.DataFrame([{v:k for k, v in r.items()} for r in res])


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
            volumes={
                f"{os.getcwd()}/{import_dir}": {
                    "bind": "/import",
                    "mode": "ro"
                }
            },
            ports={
                7474: 7474,
                7687: 7687
            }
        )
        self._created_container = True
        container_is_ready = False
        while not container_is_ready:
            try:
                res = requests.get("http://localhost:7474")
                if res.status_code == 200:
                    container_is_ready = True
            except:
                pass
            else:
                time.sleep(2)
        self.G = Graph(password="neo4jpw")

    def _teardown_container(self):
        self._running_container.stop()
        self._running_container.remove()

    def run(self, cypher: str) -> Table:
        """
        Run an arbitrary cypher command.

        You should usually ignore this, and use .find() instead.

        Arguments:
            cypher (str): The command to run

        Returns:
            The result of the cypher query

        """
        return self.G.run(cypher).to_table()

    def find(self, motif: dotmotif, limit=None) -> Table:
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif)

        """
        qry = self.motif_to_cypher(motif)
        if limit:
            qry += f" LIMIT {limit}"
        return self.G.run(qry).to_table()

    @staticmethod
    def motif_to_cypher(motif: dotmotif) -> str:
        """
        Output a query suitable for Cypher-compatible engines (e.g. Neo4j).

        Returns:
            str: A Cypher query

        """
        es = []
        es_neg = []

        motif_graph = motif.to_nx()

        for u, v, a in motif_graph.edges(data=True):
            action = motif._LOOKUP[a['action']]
            if a['exists']:
                es.append(
                    "MATCH ({}:Neuron)-[:{}]-{}({}:Neuron)".format(
                        u, action,
                        "" if motif.ignore_direction else ">",
                        v
                    )
                )
            else:
                es_neg.append(
                    "NOT ({}:Neuron)-[:{}]-{}({}:Neuron)".format(
                        u, action,
                        "" if motif.ignore_direction else ">",
                        v
                    )
                )

        delim = "\n" if motif.pretty_print else " "

        if len(es_neg):
            q_match = delim.join([delim.join(es), "WHERE " + f"{delim} AND ".join(es_neg)])
        else:
            q_match = delim.join([delim.join(es)])

        q_return = "RETURN " + ",".join(list(motif_graph.nodes()))

        if motif.limit:
            q_limit = " LIMIT {}".format(motif.limit)
        else:
            q_limit = ""

        if motif.enforce_inequality:
            q_not_eqs = "WHERE " + " AND ".join(set([
                "<>".join(sorted(a))
                for a in list(product(motif_graph.nodes(), motif_graph.nodes()))
                if a[0] != a[1]
            ]))
        else:
            return "{}".format(delim.join([q_match, q_return, q_limit]))

        return "{}".format(delim.join([q_match, q_not_eqs, q_return, q_limit]))
