import os

HOST = "neuprint.janelia.org"
DATASET = "hemibrain:v1.1"
TOKEN = os.getenv("NEUPRINT_TOKEN")

import unittest

from .. import dotmotif
from .NeuPrintExecutor import NeuPrintExecutor


class TestNeuPrintConnection(unittest.TestCase):
    def test_can_get_version(self):
        E = NeuPrintExecutor(HOST, DATASET, TOKEN)
        self.assertEqual(E.client.fetch_version(), "0.1.0")


class TestNeuPrintKnownMotifs(unittest.TestCase):
    def test_known_edge(self):
        motif = dotmotif().from_motif(
            """
            input -> output
            input.type == "KCab-p"
            """
        )
        E = NeuPrintExecutor(HOST, DATASET, TOKEN)

        self.assertTrue("ConnectsTo" in E.motif_to_cypher(motif))
        self.assertEqual(len(E.find(motif, limit=5)), 5)

    def test_bigger_motif(self):
        motif = dotmotif().from_motif(
            """
            diedge(a, b) {
                a -> b
                b !> a
                a.type == "KCab-p"
            }
            diedge(A, B)
            diedge(B, C)
            diedge(C, D)

            A !> C
            C !> A
            D !> B
            B !> D
            """
        )
        E = NeuPrintExecutor(HOST, DATASET, TOKEN)

        self.assertTrue("ConnectsTo" in E.motif_to_cypher(motif))
        print(E.motif_to_cypher(motif))
        self.assertEqual(E.count(motif, limit=50), 35)
