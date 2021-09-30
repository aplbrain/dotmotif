import unittest
import dotmotif
from dotmotif import Motif
from dotmotif.executors import GrandIsoExecutor
from dotmotif.executors.NetworkXExecutor import (
    _edge_satisfies_constraints,
    _node_satisfies_constraints,
)
from dotmotif.parsers.v2 import ParserV2
import networkx as nx


class TestSmallMotifs(unittest.TestCase):
    def test_edgecount_motif(self):
        dm = Motif("""A->B""")

        H = nx.DiGraph()
        H.add_edge("x", "y")
        self.assertEqual(len(GrandIsoExecutor(graph=H).find(dm)), 1)
        H.add_edge("x", "y")
        self.assertEqual(len(GrandIsoExecutor(graph=H).find(dm)), 1)
        H.add_edge("x", "z")
        self.assertEqual(len(GrandIsoExecutor(graph=H).find(dm)), 2)

    def test_fullyconnected_triangle_motif(self):
        dm = Motif(
            """
        A->B
        B->C
        C->A
        """
        )

        H = nx.DiGraph()
        H.add_edge("x", "y")
        self.assertEqual(len(GrandIsoExecutor(graph=H).find(dm)), 0)
        H.add_edge("y", "z")
        self.assertEqual(len(GrandIsoExecutor(graph=H).find(dm)), 0)
        H.add_edge("z", "x")
        self.assertEqual(len(GrandIsoExecutor(graph=H).find(dm)), 3)

    def test_edge_attribute_equality(self):
        dm = Motif(
            """
        A->B [weight==10, area==4]
        """
        )

        H = nx.DiGraph()
        H.add_edge("z", "x", weight=10, area=4)
        H.add_edge("x", "y")
        H.add_edge("y", "z", weight=5)
        self.assertEqual(len(GrandIsoExecutor(graph=H).find(dm)), 1)

    def test_one_instance(self):

        H = nx.DiGraph()
        H.add_edge("x", "y", weight=1)
        H.add_edge("y", "z", weight=10)
        H.add_edge("z", "x", weight=5)
        motif = dotmotif.Motif(
            """
        A -> B [weight>=11]
        """.strip()
        )

        self.assertEqual(len(GrandIsoExecutor(graph=H).find(motif)), 0)

    def test_two_instance(self):
        H = nx.DiGraph()
        H.add_edge("x", "y", weight=1)
        H.add_edge("y", "z", weight=10)
        H.add_edge("z", "x", weight=5)
        H.add_edge("z", "a", weight=5)
        H.add_edge("a", "b", weight=1)
        H.add_edge("b", "c", weight=10)
        H.add_edge("c", "a", weight=5)
        motif = dotmotif.Motif(
            """
        A -> B [weight>=7]
        """.strip()
        )

        self.assertEqual(len(GrandIsoExecutor(graph=H).find(motif)), 2)

    def test_triangle_two_instance(self):
        H = nx.DiGraph()
        H.add_edge("x", "y", weight=1)
        H.add_edge("y", "z", weight=10)
        H.add_edge("z", "x", weight=5)
        H.add_edge("z", "a", weight=5)
        H.add_edge("a", "b", weight=1)
        H.add_edge("b", "c", weight=10)
        H.add_edge("c", "a", weight=5)
        motif = dotmotif.Motif(
            """
        A -> B [weight>=7]
        B -> C
        C -> A
        """.strip()
        )

        self.assertEqual(len(GrandIsoExecutor(graph=H).find(motif)), 2)

    def test_mini_example(self):

        H = nx.DiGraph()
        H.add_edge("y", "x", ATTRIBUTE=7)
        H.add_edge("y", "z", ATTRIBUTE=7)
        motif = dotmotif.Motif(
            """
        A -> B [ATTRIBUTE>=7]
        """.strip()
        )

        self.assertEqual(len(GrandIsoExecutor(graph=H).find(motif)), 2)

    def test_node_and_edge_full_example(self):

        H = nx.DiGraph()
        H.add_edge("X", "Y", weight=10)
        H.add_edge("Y", "Z", weight=9)
        H.add_edge("Z", "X", weight=8)
        motif = dotmotif.Motif(
            """
            A -> B [weight>=7]
        """.strip()
        )

        res = GrandIsoExecutor(graph=H).find(motif)
        self.assertEqual(len(res), 3)

        H.add_edge("Z", "C", weight=7)
        res = GrandIsoExecutor(graph=H).find(motif)
        self.assertEqual(len(res), 4)

        H.add_edge("Z", "D", weight="no")
        res = GrandIsoExecutor(graph=H).find(motif)
        self.assertEqual(len(res), 4)

        H.add_edge("y", "a")
        self.assertEqual(len(GrandIsoExecutor(graph=H).find(motif)), 4)

        H.add_edge("y", "a", other_weight=7, weight=8)
        self.assertEqual(len(GrandIsoExecutor(graph=H).find(motif)), 5)

    def test_automorphism_reduction(self):

        G = nx.DiGraph()
        G.add_edge("X", "Z")
        G.add_edge("Y", "Z")

        motif = dotmotif.Motif(
            """
            A -> C
            B -> C

            A === B
            """
        )

        res = GrandIsoExecutor(graph=G).find(motif)
        self.assertEqual(len(res), 2)

        motif = dotmotif.Motif(exclude_automorphisms=True).from_motif(
            """
            A -> C
            B -> C

            A === B
            """
        )

        res = GrandIsoExecutor(graph=G).find(motif)
        self.assertEqual(len(res), 1)

    def test_automorphism_auto(self):

        G = nx.DiGraph()
        G.add_edge("X", "Z")
        G.add_edge("Y", "Z")

        motif = dotmotif.Motif(exclude_automorphisms=True).from_motif(
            """
            A -> C
            B -> C
            """
        )

        res = GrandIsoExecutor(graph=G).find(motif)
        self.assertEqual(len(res), 1)

    def test_automorphism_notauto(self):

        G = nx.DiGraph()
        G.add_edge("X", "Z")
        G.add_edge("Y", "Z")

        motif = dotmotif.Motif(
            """
            A -> C
            B -> C
            """
        )

        res = GrandIsoExecutor(graph=G).find(motif)
        self.assertEqual(len(res), 2)

    def test_automorphism_flag_triangle(self):

        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        G.add_edge("C", "A")

        motif = dotmotif.Motif(
            """
            A -> B
            B -> C
            C -> A
            """
        )
        res = GrandIsoExecutor(graph=G).find(motif)
        self.assertEqual(len(res), 3)

        motif = dotmotif.Motif(exclude_automorphisms=True).from_motif(
            """
            A -> B
            B -> C
            C -> A
            """
        )
        res = GrandIsoExecutor(graph=G).find(motif)
        self.assertEqual(len(res), 1)


class TestDynamicNodeConstraints(unittest.TestCase):
    def test_dynamic_constraints_zero_results(self):
        """
        Test that comparisons may be made between variables, e.g.:

        A.type != B.type

        """
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        G.add_edge("C", "A")
        G.add_node("A", radius=5)
        G.add_node("B", radius=10)
        exp = """\
        A -> B
        A.radius > B.radius
        """
        dm = dotmotif.Motif(parser=ParserV2)
        res = GrandIsoExecutor(graph=G).find(dm.from_motif(exp))
        self.assertEqual(len(res), 0)

    def test_dynamic_constraints_one_result(self):
        """
        Test that comparisons may be made between variables, e.g.:

        A.type != B.type

        """
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        G.add_edge("C", "A")
        G.add_node("A", radius=25)
        G.add_node("B", radius=10)
        exp = """\
        A -> B
        A.radius > B.radius
        """
        dm = dotmotif.Motif(parser=ParserV2)
        res = GrandIsoExecutor(graph=G).find(dm.from_motif(exp))
        self.assertEqual(len(res), 1)

    def test_dynamic_constraints_two_results(self):
        """
        Test that comparisons may be made between variables, e.g.:

        A.type != B.type

        """
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        G.add_edge("C", "A")
        G.add_node("A", radius=25)
        G.add_node("B", radius=10)
        G.add_node("C", radius=5)
        exp = """\
        A -> B
        A.radius > B.radius
        """
        dm = dotmotif.Motif(parser=ParserV2)
        res = GrandIsoExecutor(graph=G).find(dm.from_motif(exp))
        self.assertEqual(len(res), 2)

    def test_dynamic_constraints_in_macros_zero_results(self):
        """
        Test that comparisons may be made between variables, e.g.:

        A.type != B.type

        """
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        G.add_edge("C", "A")
        G.add_node("A", radius=5)
        G.add_node("B", radius=10)
        exp = """\
        macro(A, B) {
            A.radius > B.radius
        }
        macro(A, B)
        A -> B
        """
        dm = dotmotif.Motif(parser=ParserV2)
        res = GrandIsoExecutor(graph=G).find(dm.from_motif(exp))
        self.assertEqual(len(res), 0)

    def test_dynamic_constraints_in_macros_one_result(self):
        """
        Test that comparisons may be made between variables, e.g.:

        A.type != B.type

        """
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        G.add_edge("C", "A")
        G.add_node("A", radius=15)
        G.add_node("B", radius=10)
        exp = """\
        macro(A, B) {
            A.radius > B.radius
        }
        macro(A, B)
        A -> B
        """
        dm = dotmotif.Motif(parser=ParserV2)
        res = GrandIsoExecutor(graph=G).find(dm.from_motif(exp))
        self.assertEqual(len(res), 1)

    def test_dynamic_constraints_in_macros_two_result(self):
        """
        Test that comparisons may be made between variables, e.g.:

        A.type != B.type

        """
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        G.add_edge("C", "A")
        G.add_node("A", radius=15)
        G.add_node("B", radius=10)
        G.add_node("C", radius=10)
        exp = """\
        macro(A, B) {
            A.radius >= B.radius
        }
        macro(A, B)
        A -> B
        """
        dm = dotmotif.Motif(parser=ParserV2)
        res = GrandIsoExecutor(graph=G).find(dm.from_motif(exp))
        self.assertEqual(len(res), 2)
