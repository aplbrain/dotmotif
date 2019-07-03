import dotmotif
from dotmotif.executors.Neo4jExecutor import Neo4jExecutor
import unittest
import networkx as nx


class TestNeo4jExecutor(unittest.TestCase):
    def test_numerical_ids_fail_with_message_github_26(self):
        g = nx.DiGraph()
        g.add_edge(1, 2)
        with self.assertRaisesRegex(Exception, "numerical IDs"):
            Neo4jExecutor(graph=g)


class TestNeo4jExecutor_Automorphisms(unittest.TestCase):

    def test_basic_node_attr(self):
        exp = """\
        A -> C
        B -> C
        A === B
        """
        dm = dotmotif.dotmotif().from_motif(exp)
        cypher = Neo4jExecutor.motif_to_cypher(dm)
        self.assertIn("A.id > B.id", cypher)

    def test_automatic_autos(self):
        exp = """\
        A -> C
        B -> C
        """
        dm = dotmotif.dotmotif(exclude_automorphisms=True).from_motif(exp)
        cypher = Neo4jExecutor.motif_to_cypher(dm)
        self.assertIn("A.id >= B.id", cypher)
