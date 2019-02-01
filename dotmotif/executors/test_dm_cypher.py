"""
Test Cypher conversion system.
"""

import unittest
import dotmotif
from dotmotif.executors import Neo4jExecutor


_DEMO_G_MIN = """
A -> B
C -> A
B !- A
C !> D
"""
_DEMO_G_MIN_CYPHER = """
MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)
MATCH (C:Neuron)-[C_A:SYN]->(A:Neuron)
WHERE NOT (B:Neuron)-[B_A:INH]->(A:Neuron)
 AND NOT (C:Neuron)-[C_D:SYN]->(D:Neuron)
RETURN DISTINCT A,B,C,D
"""

_DEMO_EDGE_ATTR_CYPHER = """
MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)
MATCH (X:Neuron)-[X_Y:SYN]->(Y:Neuron)
WHERE A_B.weight = 4 AND A_B.area <= 10 AND X_Y.weight = 2
RETURN DISTINCT A,B,X,Y
"""


_DEMO_EDGE_ATTR_CYPHER_2 = """
MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)
MATCH (X:Neuron)-[X_Y:SYN]->(Y:Neuron)
WHERE A_B.weight = 4 AND A_B.area <= 10 AND A_B.area <= 20 AND X_Y.weight = 2
RETURN DISTINCT A,B,X,Y
"""


class TestDotmotif_Cypher(unittest.TestCase):
    def test_cypher(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(_DEMO_G_MIN)

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(), _DEMO_G_MIN_CYPHER.strip()
        )


class TestDotmotif_edges_Cypher(unittest.TestCase):
    def test_cypher_edge_attributes(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(
            """
        A -> B [weight=4, area<=10]
        X -> Y [weight=2]
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(), _DEMO_EDGE_ATTR_CYPHER.strip()
        )

    def test_cypher_edge_many_attributes(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(
            """
            A -> B [weight=4, area<=10, area<=20]
            X -> Y [weight=2]
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(), _DEMO_EDGE_ATTR_CYPHER_2.strip()
        )


class TestDotmotif_nodes_Cypher(unittest.TestCase):
    def test_cypher_node_attributes(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(
            """
        A -> B
        A.size = "big"
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            """MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)\nWHERE A.size = "big"\nRETURN DISTINCT A,B""".strip(),
        )

    def test_cypher_node_many_attributes(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(
            """
        A -> B
        A.size = "big"
        A.type = "funny"
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            """MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)\nWHERE A.size = "big" AND A.type = "funny"\nRETURN DISTINCT A,B""".strip(),
        )

    def test_cypher_node_same_node_many_attributes(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(
            """
        A -> B
        A.personality != "exciting"
        A.personality != "funny"
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            """MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)\nWHERE A.personality != "exciting" AND A.personality != "funny"\nRETURN DISTINCT A,B""".strip(),
        )

    def test_cypher_node_many_node_attributes(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(
            """
        A -> B
        A.area <= 10
        B.area <= 10
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            """MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)\nWHERE A.area <= 10 AND B.area <= 10\nRETURN DISTINCT A,B""".strip(),
        )
