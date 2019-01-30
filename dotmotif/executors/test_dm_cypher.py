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
MATCH (A:Neuron)-[:SYN]->(B:Neuron)
MATCH (C:Neuron)-[:SYN]->(A:Neuron)
WHERE NOT (B:Neuron)-[:INH]->(A:Neuron)
 AND NOT (C:Neuron)-[:SYN]->(D:Neuron)
RETURN DISTINCT A,B,C,D
"""


class TestDotmotif_Cypher(unittest.TestCase):
    def test_sanity(self):
        self.assertEqual(1, 1)

    def test_cypher(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(_DEMO_G_MIN)

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(), _DEMO_G_MIN_CYPHER.strip()
        )
