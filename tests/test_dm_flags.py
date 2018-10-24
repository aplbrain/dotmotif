import unittest
import dotmotif


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
WHERE NOT (C:Neuron)-[:SYN]->(D:Neuron)
RETURN A,B,C,D
"""


class TestDotmotifFlags(unittest.TestCase):

    def test_sanity(self):
        self.assertEqual(1, 1)

    def test_dm_parser_defaults(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(_DEMO_G_MIN)
        self.assertEqual(dm.to_cypher().strip(), _DEMO_G_MIN_CYPHER.strip())

    def test_dm_parser_no_pretty_print(self):
        dm = dotmotif.dotmotif(pretty_print=False)
        dm.from_motif(_DEMO_G_MIN)
        self.assertEqual(
            dm.to_cypher().strip(),
            _DEMO_G_MIN_CYPHER.strip().replace("\n", " ")
        )

    def test_dm_parser_no_direction(self):
        dm = dotmotif.dotmotif(ignore_direction=True)
        dm.from_motif(_DEMO_G_MIN)
        self.assertEqual(
            dm.to_cypher().strip(),
            _DEMO_G_MIN_CYPHER.strip().replace("->", "-")
        )

    def test_dm_parser_inequality(self):
        dm = dotmotif.dotmotif(enforce_inequality=True)
        dm.from_motif(_DEMO_G_MIN)
        self.assertTrue(
            "A<>B" in dm.to_cypher().strip() or
            "B<>A" in dm.to_cypher().strip()
        )
        self.assertTrue(
            "B<>C" in dm.to_cypher().strip() or
            "C<>B" in dm.to_cypher().strip()
        )
        self.assertTrue(
            "A<>C" in dm.to_cypher().strip() or
            "C<>A" in dm.to_cypher().strip()
        )

    def test_dm_parser_limit(self):
        dm = dotmotif.dotmotif(limit=3)
        dm.from_motif(_DEMO_G_MIN)
        self.assertTrue(
            "LIMIT 3" in dm.to_cypher().strip()
        )
        dm = dotmotif.dotmotif()
        dm.from_motif(_DEMO_G_MIN)
        self.assertFalse(
            "LIMIT" in dm.to_cypher().strip()
        )
