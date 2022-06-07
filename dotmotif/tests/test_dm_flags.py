import unittest
import dotmotif
import networkx as nx
from dotmotif.executors.Neo4jExecutor import Neo4jExecutor
from dotmotif.executors.GrandIsoExecutor import GrandIsoExecutor


_DEMO_G_MIN = """
A -> B
C -> A
B !- A
C !> D
"""
_DEMO_G_MIN_CYPHER = """
MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)
MATCH (C:Neuron)-[C_A:SYN]->(A:Neuron)
WHERE NOT (B:Neuron)-[:INH]->(A:Neuron) AND NOT (C:Neuron)-[:SYN]->(D:Neuron)
RETURN DISTINCT A,B,C,D
"""


class TestDotmotifFlags(unittest.TestCase):
    def test_sanity(self):
        self.assertEqual(1, 1)

    def test_dm_parser_defaults(self):
        dm = dotmotif.Motif()
        dm.from_motif(_DEMO_G_MIN)
        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(), _DEMO_G_MIN_CYPHER.strip()
        )

    def test_dm_parser_no_pretty_print(self):
        dm = dotmotif.Motif(pretty_print=False)
        dm.from_motif(_DEMO_G_MIN)
        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            _DEMO_G_MIN_CYPHER.strip().replace("\n", " "),
        )

    def test_dm_parser_no_direction(self):
        dm = dotmotif.Motif(ignore_direction=True)
        dm.from_motif(_DEMO_G_MIN)
        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            _DEMO_G_MIN_CYPHER.strip().replace("->", "-"),
        )

    def test_dm_parser_inequality(self):
        dm = dotmotif.Motif(enforce_inequality=True)
        dm.from_motif(_DEMO_G_MIN)
        self.assertTrue(
            "A<>B" in Neo4jExecutor.motif_to_cypher(dm).strip()
            or "B<>A" in Neo4jExecutor.motif_to_cypher(dm).strip()
        )
        self.assertTrue(
            "B<>C" in Neo4jExecutor.motif_to_cypher(dm).strip()
            or "C<>B" in Neo4jExecutor.motif_to_cypher(dm).strip()
        )
        self.assertTrue(
            "A<>C" in Neo4jExecutor.motif_to_cypher(dm).strip()
            or "C<>A" in Neo4jExecutor.motif_to_cypher(dm).strip()
        )

    def test_dm_parser_limit(self):
        dm = dotmotif.Motif(limit=3)
        dm.from_motif(_DEMO_G_MIN)
        self.assertTrue("LIMIT 3" in Neo4jExecutor.motif_to_cypher(dm).strip())
        dm = dotmotif.Motif()
        dm.from_motif(_DEMO_G_MIN)
        self.assertFalse("LIMIT" in Neo4jExecutor.motif_to_cypher(dm).strip())

    def test_from_nx_import(self):
        G = nx.Graph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")

        g = nx.Graph()
        g.add_edge("A", "B")
        dm = dotmotif.Motif().from_nx(g)

        E = GrandIsoExecutor(graph=G)
        self.assertEqual(len(E.find(dm)), 4)

    def test_from_nx_import(self):
        G = nx.Graph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")

        g = nx.Graph()
        g.add_edge("A", "B")
        dm = dotmotif.Motif(ignore_direction=True).from_nx(g)

        E = GrandIsoExecutor(graph=G)
        self.assertEqual(len(E.find(dm)), 4)


class TestPropagationOfAutomorphicConstraints(unittest.TestCase):
    def test_automorphisms(self):
        m = dotmotif.Motif(
            """
        A -> B
        B -> A

        A === B
        """
        )
        assert len(m.list_automorphisms()) == 1

    def test_constraints_propagate(self):
        m = dotmotif.Motif(
            """
        A -> B
        B -> A
        A === B
        A.radius = 5
        """
        )
        assert len(m.list_automorphisms()) == 1
        assert len(m.list_node_constraints()) == 2

    def test_constraints_propagate_multi_auto(self):
        m = dotmotif.Motif(
            """
        A -> B
        B -> A
        A -> C
        A === B
        A === C
        A.radius = 5
        """
        )
        assert len(m.list_automorphisms()) == 2
        assert len(m.list_node_constraints()) == 3
