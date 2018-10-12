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
        """

        db_bolt_uri: str = kwargs.get("db_bolt_uri", None)
        username: str = kwargs.get("username", None)
        password: str = kwargs.get("password", None)

        graph: nx.Graph = kwargs.get("graph", None)

        if db_bolt_uri and password:
            try:
                self.G = Graph(db_bolt_uri, password=password)
            except:
                raise ValueError(f"Could not connect to graph {db_bolt_uri}.")
        elif graph:
            # Export the graph to CSV (nodes and edges):
            nodes_csv = "neuronId:ID(Neuron)\n" + "\n".join([
                i for i, n in
                graph.nodes(True)
            ])
            edges_csv = ":START_ID(Neuron),:END_ID(Neuron)\n" + "\n".join([
                f"{u},{v}" for u, v in
                graph.edges()
            ])

            # Export the files:
            try:
                os.makedirs("export-custom-graph")
            except:
                pass
            with open("export-custom-graph/export-neurons-0.csv", 'w') as fh:
                fh.write(nodes_csv)
            with open("export-custom-graph/export-synapses-0.csv", 'w') as fh:
                fh.write(edges_csv)

            # Create a docker container:
            self.docker_client = docker.from_env()
            self._running_container = self.docker_client.containers.run(
                "neo4j:3.4",
                # auto_remove=True,
                detach=True,
                volumes={
                    f"{os.getcwd()}/export-custom-graph": {
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
            # TODO: wait for running
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
        else:
            raise ValueError(
                "You must supply either an existing db or a graph to load."
            )

    def __del__(self):
        if self._created_container:
            self._teardown_container()

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
