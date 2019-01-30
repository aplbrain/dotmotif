
import unittest
import dotmotif
from dotmotif.executors import NetworkXExecutor
import networkx as nx


class TestSmallMotifs(unittest.TestCase):

    def test_edgecount_motif(self):
        dm = dotmotif.dotmotif()
        dm.from_motif("""A->B""")

        H = nx.DiGraph()
        H.add_edge("x", "y")
        self.assertEqual(
            len(NetworkXExecutor(graph=H).find(dm)),
            1
        )
        H.add_edge("x", "y")
        self.assertEqual(
            len(NetworkXExecutor(graph=H).find(dm)),
            1
        )
        H.add_edge("x", "z")
        self.assertEqual(
            len(NetworkXExecutor(graph=H).find(dm)),
            2
        )

    def test_fullyconnected_triangle_motif(self):
        dm = dotmotif.dotmotif()
        dm.from_motif("""
        A->B
        B->C
        C->A
        """)

        H = nx.DiGraph()
        H.add_edge("x", "y")
        self.assertEqual(
            len(NetworkXExecutor(graph=H).find(dm)),
            0
        )
        H.add_edge("y", "z")
        self.assertEqual(
            len(NetworkXExecutor(graph=H).find(dm)),
            0
        )
        H.add_edge("z", "x")
        self.assertEqual(
            len(NetworkXExecutor(graph=H).find(dm)),
            3
        )

    def test_edge_attribute_equality(self):
        dm = dotmotif.dotmotif()
        dm.from_motif("""
        A->B [weight==10, area==4]
        """)

        H = nx.DiGraph()
        H.add_edge("z", "x", weight=10, area=4)
        H.add_edge("x", "y")
        H.add_edge("y", "z", weight=5)
        self.assertEqual(
            len(NetworkXExecutor(graph=H).find(dm)),
            1
        )
