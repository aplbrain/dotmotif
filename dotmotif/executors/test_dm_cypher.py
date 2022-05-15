"""
Test Cypher conversion system.

Doesn't check validity of output; just matchiness to test strings.
"""

import unittest
import dotmotif
from dotmotif.executors.Neo4jExecutor import Neo4jExecutor


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

_DEMO_EDGE_ATTR_CYPHER = """
MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)
MATCH (X:Neuron)-[X_Y:SYN]->(Y:Neuron)
WHERE A_B["weight"] = 4 AND A_B["area"] <= 10 AND X_Y["weight"] = 2
RETURN DISTINCT A,B,X,Y
"""


_DEMO_EDGE_ATTR_CYPHER_2 = """
MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)
MATCH (X:Neuron)-[X_Y:SYN]->(Y:Neuron)
WHERE A_B["weight"] = 4 AND A_B["area"] <= 10 AND A_B["area"] <= 20 AND X_Y["weight"] = 2
RETURN DISTINCT A,B,X,Y
"""

_DEMO_EDGE_ATTR_CYPHER_2_ENF_INEQ = """
MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)
MATCH (X:Neuron)-[X_Y:SYN]->(Y:Neuron)
WHERE A_B["weight"] = 4 AND A_B["area"] <= 10 AND A_B["area"] <= 20 AND X_Y["weight"] = 2 AND B<>X AND B<>Y AND A<>X AND A<>B AND A<>Y AND X<>Y
RETURN DISTINCT A,B,X,Y
"""


class TestDotmotif_Cypher(unittest.TestCase):
    def test_cypher(self):
        dm = dotmotif.Motif()
        dm.from_motif(_DEMO_G_MIN)
        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(), _DEMO_G_MIN_CYPHER.strip()
        )


class TestDotmotif_edges_Cypher(unittest.TestCase):
    def test_cypher_edge_attributes(self):
        dm = dotmotif.Motif()
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
        dm = dotmotif.Motif()
        dm.from_motif(
            """
            A -> B [weight=4, area<=10, area<=20]
            X -> Y [weight=2]
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(), _DEMO_EDGE_ATTR_CYPHER_2.strip()
        )

    #   TODO      # Issue with arbitrary ordering of inequalities
    # def test_cypher_edge_many_attributes_and_enforce_inequality(self):
    #     dm = dotmotif.Motif(enforce_inequality=True)
    #     dm.from_motif(
    #         """
    #         A -> B [weight=4, area<=10, area<=20]
    #         X -> Y [weight=2]
    #     """
    #     )

    #     self.assertEqual(
    #         Neo4jExecutor.motif_to_cypher(dm).strip(),
    #         _DEMO_EDGE_ATTR_CYPHER_2_ENF_INEQ.strip(),
    #     )


class TestDotmotif_nodes_Cypher(unittest.TestCase):
    def test_cypher_node_attributes(self):
        dm = dotmotif.Motif()
        dm.from_motif(
            """
        A -> B
        A.size = "big"
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            """MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)\nWHERE A["size"] = "big"\nRETURN DISTINCT A,B""".strip(),
        )

    def test_cypher_node_many_attributes(self):
        dm = dotmotif.Motif()
        dm.from_motif(
            """
        A -> B
        A.size = "big"
        A.type = "funny"
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            """MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)\nWHERE A["size"] = "big" AND A["type"] = "funny"\nRETURN DISTINCT A,B""".strip(),
        )

    def test_cypher_node_same_node_many_attributes(self):
        dm = dotmotif.Motif()
        dm.from_motif(
            """
        A -> B
        A.personality != "exciting"
        A.personality != "funny"
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            """MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)\nWHERE A["personality"] <> "exciting" AND A["personality"] <> "funny"\nRETURN DISTINCT A,B""".strip(),
        )

    def test_cypher_node_many_node_attributes(self):
        dm = dotmotif.Motif()
        dm.from_motif(
            """
        A -> B
        A.area <= 10
        B.area <= 10
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            """MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)\nWHERE A["area"] <= 10 AND B["area"] <= 10\nRETURN DISTINCT A,B""".strip(),
        )

    def test_cypher_negative_edge_and_inequality(self):
        dm = dotmotif.Motif(enforce_inequality=True)
        dm.from_motif(
            """
        A -> B
        A -> C
        B !> C
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            (
                "MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)\n"
                "MATCH (A:Neuron)-[A_C:SYN]->(C:Neuron)\n"
                "WHERE NOT (B:Neuron)-[:SYN]->(C:Neuron) AND A<>B AND A<>C AND B<>C\n"
                "RETURN DISTINCT A,B,C"
            ).strip(),
        )


class TestDotmotif_nodes_edges_Cypher(unittest.TestCase):
    def test_cypher_node_and_edge_attributes(self):
        dm = dotmotif.Motif()
        dm.from_motif(
            """
        A -> B [area != 10]
        A.area <= 10
        B.area <= 10
        """
        )

        self.assertEqual(
            Neo4jExecutor.motif_to_cypher(dm).strip(),
            (
                "MATCH (A:Neuron)-[A_B:SYN]->(B:Neuron)\n"
                'WHERE A["area"] <= 10 AND B["area"] <= 10 AND A_B["area"] <> 10\n'
                "RETURN DISTINCT A,B"
            ).strip(),
        )


class TestDynamicNodeConstraints(unittest.TestCase):
    def test_dynamic_constraints_in_cypher(self):
        dm = dotmotif.Motif(enforce_inequality=True)
        dm.from_motif(
            """
        A -> B
        A.radius >= B.radius
        A.zorf != B.zorf
        """
        )
        self.assertIn(
            """WHERE A["radius"] >= B["radius"] AND A["zorf"] <> B["zorf"]""",
            Neo4jExecutor.motif_to_cypher(dm).strip(),
        )


class BugReports(unittest.TestCase):
    def test_fix_where_clause__github_35(self):
        dm = dotmotif.Motif(enforce_inequality=True)
        dm.from_motif(
            """
        A -> B
        """
        )
        self.assertIn("WHERE", Neo4jExecutor.motif_to_cypher(dm).strip())
