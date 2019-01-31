import unittest
import dotmotif
from dotmotif.executors import NetworkXExecutor
from dotmotif.executors.NetworkXExecutor import _edge_satisfies_constraints
import networkx as nx


class TestEdgeConstraints(unittest.TestCase):

    def test_edge_satisfies(self):
        constraints = {"weight": {"==": 10}}
        edge = {"weight": 10}

        self.assertTrue(_edge_satisfies_constraints(
            edge, constraints
        ))

    def test_edge_not_satisfies(self):
        constraints = {"weight": {"!=": 10}}
        edge = {"weight": 10}

        self.assertFalse(_edge_satisfies_constraints(
            edge, constraints
        ))

    def test_edge_many_satisfies(self):
        constraints = {
            "weight": {"!=": 10, "==": 9}
        }
        edge = {"weight": 9.0}

        self.assertTrue(_edge_satisfies_constraints(
            edge, constraints
        ))

    def test_edge_many_not_satisfies(self):
        constraints = {
            "weight": {"!=": 10, "==": 9},
            "mode": {"==": "normal"}
        }
        edge = {"weight": 9, "mode": "normal"}

        self.assertTrue(_edge_satisfies_constraints(
            edge, constraints
        ))

        edge = {"mode": "normal"}

        self.assertFalse(_edge_satisfies_constraints(
            edge, constraints
        ))

    def test_edge_many_some_not_satisfies(self):
        constraints = {
            "weight": {"!=": 10, "==": 9},
            "mode": {"==": "normal"}
        }
        edge = {"weight": 10.0}

        self.assertFalse(_edge_satisfies_constraints(
            edge, constraints
        ))

        edge = {"mode": "abnormal"}

        self.assertFalse(_edge_satisfies_constraints(
            edge, constraints
        ))

    def test_nx_edges(self):
        constraints = {
            "weight": {">=": 7},
        }

        H = nx.DiGraph()
        H.add_edge("y", "x", weight=10)
        H.add_edge("a", "x", weight=7.0)

        for _, _, a in H.edges(data=True):
            self.assertTrue(_edge_satisfies_constraints(
            a, constraints
        ))

        H = nx.DiGraph()
        H.add_edge("y", "x", weight=4)
        H.add_edge("a", "x", weight=3.0)

        for _, _, a in H.edges(data=True):
            self.assertFalse(_edge_satisfies_constraints(
            a, constraints
        ))


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

    def test_mini_example(self):

        H = nx.DiGraph()
        H.add_edge("y", "x", weight=10)
        H.add_edge("x", "z", weight=1)
        # H.add_edge("x", "a", weight=2)
        H.add_edge("a", "b", weight=5)
        H.add_edge("a", "x", weight=7)
        H.add_edge("z", "y", weight=2)
        H.add_edge("z", "b", weight=0)
        H.add_edge("z", "a", weight=5)
        motif = dotmotif.dotmotif().from_motif("""
        A -> B [weight>=7]
        """.strip())

        self.assertEqual(
            len(NetworkXExecutor(graph=H).find(motif)),
            2
        )
