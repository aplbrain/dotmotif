# Standard imports
import time
import os

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


class NetworkXExecutor:

    def __init__(self, **kwargs) -> None:
        """
        """
        if 'graph' in kwargs:
            self.graph = kwargs.get('graph')
        else:
            raise ValueError(
                "You must pass a graph to the NetworkXExecutor constructor."
            )

    def find(self, motif, limit=None):
        gm = nx.algorithms.isomorphism.GraphMatcher(self.graph, motif.to_nx())
        res = gm.subgraph_isomorphisms_iter()
        return pd.DataFrame([{v:k for k, v in r.items()} for r in res])


class Neo4jExecutor:
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
        username: str = kwargs.get("username", None)
        password: str = kwargs.get("password", None)

        graph: nx.Graph = kwargs.get("graph", None)
        import_directory: str = kwargs.get("import_directory", None)

        if db_bolt_uri and password:
            # Authentication information was provided. Use this to log in and
            # connect to the existing database.
            self._connect_to_existing_graph(db_bolt_uri, password)

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
                raise ValueError("Could not export graph: {e}")

            self._create_container(export_dir)

        else:
            raise ValueError(
                "You must supply either an existing db or a graph to load."
            )

    def __del__(self):
        if self._created_container:
            self._teardown_container()

    def _connect_to_existing_graph(
        self, db_bolt_uri: str, password: str
    ) -> None:
        try:
            self.G = Graph(db_bolt_uri, password=password)
        except:
            raise ValueError(f"Could not connect to graph {db_bolt_uri}.")

    def _create_container(self, import_dir: str):
        # Create a docker container:
        self.docker_client = docker.from_env()
        self._running_container = self.docker_client.containers.run(
            "neo4j:3.4",
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
        self.G = Graph(password="neo4j")
        self.G.run("CALL dbms.changePassword('neo4jpw')").to_table()
        self._ingest_data()

    def _ingest_data(self):
        if not self._created_container:
            raise ValueError("Cannot ingest data until database is running.")
        # self.G.run("""
        # LOAD CSV WITH HEADERS FROM "file:/export-neurons-0.csv" AS line
        # CREATE (:Neuron { id: line.neuronId })
        # """)
        self.G.run("""
        LOAD CSV WITH HEADERS FROM "file:/export-synapses-0.csv" AS line
        MERGE (n:Neuron {id : line.`:START_ID(Neuron)`})
        WITH line, n
        MERGE (m:Neuron {id : line.`:END_ID(Neuron)`})
        WITH m,n
        MERGE (n)-[:SYN]->(m);
        """)

    def _teardown_container(self):
        self._running_container.stop()
        self._running_container.remove()

    def run(self, cypher: str) -> Table:
        return self.G.run(cypher).to_table()

    def find(self, motif: 'dotmotif', limit=None) -> Table:
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif)

        """
        qry = motif.to_cypher()
        if limit:
            qry += f" LIMIT {limit}"
        return self.G.run(qry).to_table()
