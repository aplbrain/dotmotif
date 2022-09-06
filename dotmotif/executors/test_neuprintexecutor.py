import os

HOST = "neuprint.janelia.org"
DATASET = "hemibrain:v1.1"
TOKEN = os.getenv("NEUPRINT_TOKEN")
if TOKEN:

    import unittest

    from .. import Motif
    from .NeuPrintExecutor import NeuPrintExecutor

    class TestNeuPrintConnection(unittest.TestCase):
        def test_can_get_version(self):
            E = NeuPrintExecutor(HOST, DATASET, TOKEN)
            self.assertEqual(E.client.fetch_version(), "0.1.0")

    class TestNeuPrintKnownMotifs(unittest.TestCase):
        def test_known_edge(self):
            motif = Motif().from_motif(
                """
                input -> output
                input.type == "KCab-p"
                """
            )
            E = NeuPrintExecutor(HOST, DATASET, TOKEN)

            self.assertTrue("ConnectsTo" in E.motif_to_cypher(motif))
            self.assertEqual(len(E.find(motif, limit=5)), 5)

        def test_bigger_motif(self):
            motif = Motif().from_motif(
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

        def test_edge_constraints_notation1(self):
            motif = Motif().from_motif(
                """
                A -> B as AB
                AB["CRE(L).pre"] > 10
                AB["CX.post"] > 20
                """
            )
            E = NeuPrintExecutor(HOST, DATASET, TOKEN)
            print(E.motif_to_cypher(motif))
            self.assertTrue(len(E.find(motif=motif, limit=5)) == 5)

        def test_edge_constraints_notation2(self):
            motif = Motif().from_motif(
                """
                A -> B ["CRE(L).pre" > 10, "CX.post" > 20]
                """
            )
            E = NeuPrintExecutor(HOST, DATASET, TOKEN)
            print(E.motif_to_cypher(motif))
            self.assertTrue(len(E.find(motif=motif, limit=5)) == 5)