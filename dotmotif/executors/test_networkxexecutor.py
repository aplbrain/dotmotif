import unittest
import dotmotif
from dotmotif.executors import NetworkXExecutor
from dotmotif.executors.NetworkXExecutor import (
    _edge_satisfies_constraints,
    _node_satisfies_constraints,
)
from dotmotif.parsers.v2 import ParserV2
import networkx as nx


class TestNodeConstraintsSatisfy(unittest.TestCase):
    def test_edge_satisfies_eq(self):
        constraints = {"radius": {"==": [10]}}
        node = {"radius": 10}
        self.assertTrue(_node_satisfies_constraints(node, constraints))
        constraints = {"radius": {"==": [-10.5]}}
        node = {"radius": -21 / 2}
        self.assertTrue(_node_satisfies_constraints(node, constraints))


class TestEdgeConstraintsSatisfy(unittest.TestCase):
    def test_edge_satisfies_eq(self):
        constraints = {"weight": {"==": [10]}}
        edge = {"weight": 10}
        self.assertTrue(_edge_satisfies_constraints(edge, constraints))
        constraints = {"weight": {"==": [-10.5]}}
        edge = {"weight": -21 / 2}
        self.assertTrue(_edge_satisfies_constraints(edge, constraints))

    def test_edge_satisfies_gte(self):
        constraints = {"weight": {">=": [10]}}
        edge = {"weight": 10}
        self.assertTrue(_edge_satisfies_constraints(edge, constraints))
        constraints = {"weight": {">=": [10]}}
        edge = {"weight": 100}
        self.assertTrue(_edge_satisfies_constraints(edge, constraints))

    def test_edge_satisfies_lte(self):
        constraints = {"weight": {"<=": [10]}}
        edge = {"weight": 10}
        self.assertTrue(_edge_satisfies_constraints(edge, constraints))
        constraints = {"weight": {"<=": [10]}}
        edge = {"weight": -100}
        self.assertTrue(_edge_satisfies_constraints(edge, constraints))

    def test_edge_satisfies_gt(self):
        constraints = {"weight": {">": [10]}}
        edge = {"weight": 100}
        self.assertTrue(_edge_satisfies_constraints(edge, constraints))

    def test_edge_satisfies_lt(self):
        constraints = {"weight": {"<": [10]}}
        edge = {"weight": -100}
        self.assertTrue(_edge_satisfies_constraints(edge, constraints))

    def test_edge_neq(self):
        constraints = {"weight": {"!=": [10]}}
        edge = {"weight": 11}
        self.assertTrue(_edge_satisfies_constraints(edge, constraints))
        constraints = {"weight": {"!=": [10]}}
        edge = {"weight": "TURTLE"}
        self.assertTrue(_edge_satisfies_constraints(edge, constraints))


class TestEdgeConstraintsNotSatisfy(unittest.TestCase):
    def test_edge_satisfies_eq(self):
        constraints = {"weight": {"==": [10]}}
        edge = {"weight": 11}
        self.assertFalse(_edge_satisfies_constraints(edge, constraints))
        constraints = {"weight": {"==": [-10.5]}}
        edge = {"weight": -21 / 3}
        self.assertFalse(_edge_satisfies_constraints(edge, constraints))

    def test_edge_satisfies_gte(self):
        constraints = {"weight": {">=": [10]}}
        edge = {"weight": 9}
        self.assertFalse(_edge_satisfies_constraints(edge, constraints))
        constraints = {"weight": {">=": [10]}}
        edge = {"weight": -100}
        self.assertFalse(_edge_satisfies_constraints(edge, constraints))

    def test_edge_satisfies_lte(self):
        constraints = {"weight": {"<=": [10]}}
        edge = {"weight": 100}
        self.assertFalse(_edge_satisfies_constraints(edge, constraints))
        constraints = {"weight": {"<=": [10]}}
        edge = {"weight": 100}
        self.assertFalse(_edge_satisfies_constraints(edge, constraints))

    def test_edge_satisfies_gt(self):
        constraints = {"weight": {">": [10]}}
        edge = {"weight": 1}
        self.assertFalse(_edge_satisfies_constraints(edge, constraints))

    def test_edge_satisfies_lt(self):
        constraints = {"weight": {"<": [10]}}
        edge = {"weight": 10}
        self.assertFalse(_edge_satisfies_constraints(edge, constraints))

    def test_edge_neq(self):
        constraints = {"weight": {"!=": [10]}}
        edge = {"weight": 10}
        self.assertFalse(_edge_satisfies_constraints(edge, constraints))
        constraints = {"weight": {"!=": ["TURTLE"]}}
        edge = {"weight": "TURTLE"}
        self.assertFalse(_edge_satisfies_constraints(edge, constraints))

    def test_edge_many_satisfies(self):
        constraints = {"weight": {"!=": [10], "==": [9]}}
        edge = {"weight": 9.0}

        self.assertTrue(_edge_satisfies_constraints(edge, constraints))

    def test_edge_many_not_satisfies(self):
        constraints = {"weight": {"!=": [10], "==": [9]}, "mode": {"==": ["normal"]}}
        edge = {"weight": 9, "mode": "normal"}

        self.assertTrue(_edge_satisfies_constraints(edge, constraints))

        edge = {"mode": "normal"}

        self.assertFalse(_edge_satisfies_constraints(edge, constraints))

    def test_edge_many_some_not_satisfies(self):
        constraints = {"weight": {"!=": [10], "==": [9]}, "mode": {"==": "normal"}}
        edge = {"weight": 10.0}

        self.assertFalse(_edge_satisfies_constraints(edge, constraints))

        edge = {"mode": "abnormal"}

        self.assertFalse(_edge_satisfies_constraints(edge, constraints))

    def test_nx_edges(self):
        constraints = {"weight": {">=": [7]}}

        H = nx.DiGraph()
        H.add_edge("y", "x", weight=10)
        H.add_edge("a", "x", weight=7.0)

        for _, _, a in H.edges(data=True):
            self.assertTrue(_edge_satisfies_constraints(a, constraints))

        H = nx.DiGraph()
        H.add_edge("y", "x", weight=4)
        H.add_edge("a", "x", weight=3.0)

        for _, _, a in H.edges(data=True):
            self.assertFalse(_edge_satisfies_constraints(a, constraints))

    def test_contains(self):
        constraints = {"name": {"contains": ["oodle"]}}

        H = nx.DiGraph()
        H.add_edge("y", "z", name="poodle")
        H.add_edge("a", "b", name="Doodles")

        for _, _, a in H.edges(data=True):
            self.assertTrue(_edge_satisfies_constraints(a, constraints))

        H = nx.DiGraph()
        H.add_edge("y", "z", name="puddle")
        H.add_edge("a", "b", name="DOodles")

        for _, _, a in H.edges(data=True):
            self.assertFalse(_edge_satisfies_constraints(a, constraints))

    def test_in(self):
        constraints = {"name": {"in": [["A", "B"]]}}

        H = nx.DiGraph()
        H.add_edge("y", "z", name="A")
        H.add_edge("a", "b", name="B")

        for _, _, a in H.edges(data=True):
            self.assertTrue(_edge_satisfies_constraints(a, constraints))

        H = nx.DiGraph()
        H.add_edge("y", "z", name="C")
        H.add_edge("a", "b", name="['A']")

        for _, _, a in H.edges(data=True):
            self.assertFalse(_edge_satisfies_constraints(a, constraints))

    def test_in_string(self):
        constraints = {"name": {"in": ["abcdefghijklmnopqrstuvwxyz"]}}

        H = nx.DiGraph()
        H.add_edge("y", "z", name="cde")
        H.add_edge("a", "b", name="jklm")

        for _, _, a in H.edges(data=True):
            self.assertTrue(_edge_satisfies_constraints(a, constraints))


class TestSmallMotifs(unittest.TestCase):
    def test_edgecount_motif(self):
        dm = dotmotif.dotmotif()
        dm.from_motif("""A->B""")

        H = nx.DiGraph()
        H.add_edge("x", "y")
        self.assertEqual(len(NetworkXExecutor(graph=H).find(dm)), 1)
        H.add_edge("x", "y")
        self.assertEqual(len(NetworkXExecutor(graph=H).find(dm)), 1)
        H.add_edge("x", "z")
        self.assertEqual(len(NetworkXExecutor(graph=H).find(dm)), 2)

    def test_fullyconnected_triangle_motif(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(
            """
        A->B
        B->C
        C->A
        """
        )

        H = nx.DiGraph()
        H.add_edge("x", "y")
        self.assertEqual(len(NetworkXExecutor(graph=H).find(dm)), 0)
        H.add_edge("y", "z")
        self.assertEqual(len(NetworkXExecutor(graph=H).find(dm)), 0)
        H.add_edge("z", "x")
        self.assertEqual(len(NetworkXExecutor(graph=H).find(dm)), 3)

    def test_edge_attribute_equality(self):
        dm = dotmotif.dotmotif()
        dm.from_motif(
            """
        A->B [weight==10, area==4]
        """
        )

        H = nx.DiGraph()
        H.add_edge("z", "x", weight=10, area=4)
        H.add_edge("x", "y")
        H.add_edge("y", "z", weight=5)
        self.assertEqual(len(NetworkXExecutor(graph=H).find(dm)), 1)

    def test_one_instance(self):

        H = nx.DiGraph()
        H.add_edge("x", "y", weight=1)
        H.add_edge("y", "z", weight=10)
        H.add_edge("z", "x", weight=5)
        motif = dotmotif.dotmotif().from_motif(
            """
        A -> B [weight>=11]
        """.strip()
        )

        self.assertEqual(len(NetworkXExecutor(graph=H).find(motif)), 0)

    def test_two_instance(self):
        H = nx.DiGraph()
        H.add_edge("x", "y", weight=1)
        H.add_edge("y", "z", weight=10)
        H.add_edge("z", "x", weight=5)
        H.add_edge("z", "a", weight=5)
        H.add_edge("a", "b", weight=1)
        H.add_edge("b", "c", weight=10)
        H.add_edge("c", "a", weight=5)
        motif = dotmotif.dotmotif().from_motif(
            """
        A -> B [weight>=7]
        """.strip()
        )

        self.assertEqual(len(NetworkXExecutor(graph=H).find(motif)), 2)

    def test_triangle_two_instance(self):
        H = nx.DiGraph()
        H.add_edge("x", "y", weight=1)
        H.add_edge("y", "z", weight=10)
        H.add_edge("z", "x", weight=5)
        H.add_edge("z", "a", weight=5)
        H.add_edge("a", "b", weight=1)
        H.add_edge("b", "c", weight=10)
        H.add_edge("c", "a", weight=5)
        motif = dotmotif.dotmotif().from_motif(
            """
        A -> B [weight>=7]
        B -> C
        C -> A
        """.strip()
        )

        self.assertEqual(len(NetworkXExecutor(graph=H).find(motif)), 2)

    def test_mini_example(self):

        H = nx.DiGraph()
        H.add_edge("y", "x", ATTRIBUTE=7)
        H.add_edge("y", "z", ATTRIBUTE=7)
        motif = dotmotif.dotmotif().from_motif(
            """
        A -> B [ATTRIBUTE>=7]
        """.strip()
        )

        self.assertEqual(len(NetworkXExecutor(graph=H).find(motif)), 2)

    def test_node_and_edge_full_example(self):

        H = nx.DiGraph()
        H.add_edge("X", "Y", weight=10)
        H.add_edge("Y", "Z", weight=9)
        H.add_edge("Z", "X", weight=8)
        motif = dotmotif.dotmotif().from_motif(
            """
            A -> B [weight>=7]
        """.strip()
        )

        res = NetworkXExecutor(graph=H).find(motif)
        self.assertEqual(len(res), 3)

        H.add_edge("Z", "C", weight=7)
        res = NetworkXExecutor(graph=H).find(motif)
        self.assertEqual(len(res), 4)

        H.add_edge("Z", "D", weight="no")
        res = NetworkXExecutor(graph=H).find(motif)
        self.assertEqual(len(res), 4)

        H.add_edge("y", "a")
        self.assertEqual(len(NetworkXExecutor(graph=H).find(motif)), 4)

        H.add_edge("y", "a", other_weight=7, weight=8)
        self.assertEqual(len(NetworkXExecutor(graph=H).find(motif)), 5)

    def test_automorphism_reduction(self):

        G = nx.DiGraph()
        G.add_edge("X", "Z")
        G.add_edge("Y", "Z")

        motif = dotmotif.dotmotif().from_motif(
            """
            A -> C
            B -> C

            A === B
            """
        )

        res = NetworkXExecutor(graph=G).find(motif)
        self.assertEqual(len(res), 2)

        motif = dotmotif.dotmotif(exclude_automorphisms=True).from_motif(
            """
            A -> C
            B -> C

            A === B
            """
        )

        res = NetworkXExecutor(graph=G).find(motif)
        self.assertEqual(len(res), 1)

    def test_automorphism_auto(self):

        G = nx.DiGraph()
        G.add_edge("X", "Z")
        G.add_edge("Y", "Z")

        motif = dotmotif.dotmotif(exclude_automorphisms=True).from_motif(
            """
            A -> C
            B -> C
            """
        )

        res = NetworkXExecutor(graph=G).find(motif)
        self.assertEqual(len(res), 1)

    def test_automorphism_notauto(self):

        G = nx.DiGraph()
        G.add_edge("X", "Z")
        G.add_edge("Y", "Z")

        motif = dotmotif.dotmotif().from_motif(
            """
            A -> C
            B -> C
            """
        )

        res = NetworkXExecutor(graph=G).find(motif)
        self.assertEqual(len(res), 2)

    def test_automorphism_flag_triangle(self):

        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        G.add_edge("C", "A")

        motif = dotmotif.dotmotif().from_motif(
            """
            A -> B
            B -> C
            C -> A
            """
        )
        res = NetworkXExecutor(graph=G).find(motif)
        self.assertEqual(len(res), 3)

        motif = dotmotif.dotmotif(exclude_automorphisms=True).from_motif(
            """
            A -> B
            B -> C
            C -> A
            """
        )
        res = NetworkXExecutor(graph=G).find(motif)
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
        dm = dotmotif.dotmotif(parser=ParserV2)
        res = NetworkXExecutor(graph=G).find(dm.from_motif(exp))
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
        dm = dotmotif.dotmotif(parser=ParserV2)
        res = NetworkXExecutor(graph=G).find(dm.from_motif(exp))
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
        dm = dotmotif.dotmotif(parser=ParserV2)
        res = NetworkXExecutor(graph=G).find(dm.from_motif(exp))
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
        dm = dotmotif.dotmotif(parser=ParserV2)
        res = NetworkXExecutor(graph=G).find(dm.from_motif(exp))
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
        dm = dotmotif.dotmotif(parser=ParserV2)
        res = NetworkXExecutor(graph=G).find(dm.from_motif(exp))
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
        dm = dotmotif.dotmotif(parser=ParserV2)
        res = NetworkXExecutor(graph=G).find(dm.from_motif(exp))
        self.assertEqual(len(res), 2)


class TestNotInAndNotContains(unittest.TestCase):
    def test_not_contains(self):
        m = dotmotif.Motif(
            """
        A -> B
        A.name !contains "foo"
        """
        )

        host = nx.DiGraph()
        host.add_edge("A", "B")
        host.add_edge("B", "A")
        host.add_node("A", name="the foobar")
        host.add_node("B", name="Barbaz")

        res = NetworkXExecutor(graph=host).find(m)
        self.assertEqual(len(res), 1)

    def test_not_in(self):
        m = dotmotif.Motif(
            """
        A -> B
        A.name !in "foo"
        """
        )

        host = nx.DiGraph()
        host.add_edge("A", "B")
        host.add_node("A", name="the foobar")
        host.add_node("B", name="Barbaz")

        res = NetworkXExecutor(graph=host).find(m)
        self.assertEqual(len(res), 1)
