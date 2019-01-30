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
WHERE A_B.weight = 4.0 AND A_B.area <= 10.0 AND X_Y.weight = 2.0
RETURN DISTINCT A,B,X,Y
"""


class TestDotmotif_Cypher(unittest.TestCase):

    def test_cypher(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(_DEMO_G_MIN)

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(), _DEMO_G_MIN_CYPHER.strip()
        )

    def test_cypher_edge_attributes(self):
        dm = dotmotif.dotmotif()
        dm.from_motif("""
        A -> B [weight=4, area<=10]
        X -> Y [weight=2]
        """)

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            _DEMO_EDGE_ATTR_CYPHER.strip()
        )
