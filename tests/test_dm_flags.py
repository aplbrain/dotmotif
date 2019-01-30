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


class TestDotmotifFlags(unittest.TestCase):
    def test_sanity(self):
        self.assertEqual(1, 1)

    def test_dm_parser_defaults(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(_DEMO_G_MIN)
        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(), _DEMO_G_MIN_CYPHER.strip()
        )

    def test_dm_parser_no_pretty_print(self):
        dm = dotmotif.dotmotif(pretty_print=False)
        dm.from_motif(_DEMO_G_MIN)
        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            _DEMO_G_MIN_CYPHER.strip().replace("\n", " "),
        )

    def test_dm_parser_no_direction(self):
        dm = dotmotif.dotmotif(ignore_direction=True)
        dm.from_motif(_DEMO_G_MIN)
        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            _DEMO_G_MIN_CYPHER.strip().replace("->", "-"),
        )

    def test_dm_parser_inequality(self):
        dm = dotmotif.dotmotif(enforce_inequality=True)
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
        dm = dotmotif.dotmotif(limit=3)
        dm.from_motif(_DEMO_G_MIN)
        self.assertTrue("LIMIT 3" in Neo4jExecutor.motif_to_cypher(dm).strip())
        dm = dotmotif.dotmotif()
        dm.from_motif(_DEMO_G_MIN)
        self.assertFalse("LIMIT" in Neo4jExecutor.motif_to_cypher(dm).strip())
