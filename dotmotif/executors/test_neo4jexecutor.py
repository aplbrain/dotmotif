from dotmotif.executors.Neo4jExecutor import Neo4jExecutor
import unittest
import networkx as nx


class TestNeo4jExecutor(unittest.TestCase):
    def test_numerical_ids_fail_with_message_github_26(self):
        g = nx.DiGraph()
        g.add_edge(1, 2)
        with self.assertRaisesRegex(Exception, "numerical IDs"):
            Neo4jExecutor(graph=g)
