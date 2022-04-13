import dotmotif
from dotmotif.executors.Neo4jExecutor import Neo4jExecutor, _quoted_if_necessary
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
        dm = dotmotif.Motif(exp)
        cypher = Neo4jExecutor.motif_to_cypher(dm)
        self.assertIn("id(A) < id(B)", cypher)

    def test_automatic_autos(self):
        exp = """\
        A -> C
        B -> C
        """
        dm = dotmotif.Motif(exp, exclude_automorphisms=True)
        cypher = Neo4jExecutor.motif_to_cypher(dm)
        self.assertIn("id(A) < id(B)", cypher)


class TestQuotingIfNecessary(unittest.TestCase):
    def test_quoting_if_necessary(self):
        self.assertEqual(_quoted_if_necessary('"xyz"'), '"xyz"'),
        self.assertEqual(_quoted_if_necessary("'xyz'"), "'xyz'"),
        self.assertEqual(_quoted_if_necessary("""x'y"z"""), '''"x'y\\\"z"'''),
        self.assertEqual(_quoted_if_necessary('foo "bar"'), "'foo \"bar\"'"),
        self.assertEqual(_quoted_if_necessary("""don't break"""), '''"don't break"'''),
        self.assertEqual(_quoted_if_necessary("foo bar"), '"foo bar"')
        self.assertEqual(_quoted_if_necessary("foo"), '"foo"')
