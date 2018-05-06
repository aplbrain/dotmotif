import unittest
import dotmotif


class TestDotmotif_Illegal(unittest.TestCase):

    def test_disagreeing_edges(self):
        dm = dotmotif.dotmotif()
        with self.assertRaises(dotmotif.MotifError):
            dm.from_motif("A -- B\nA !- B")

    def test_disagreeing_edges_notational(self):
        dm = dotmotif.dotmotif()
        with self.assertRaises(dotmotif.MotifError):
            dm.from_motif("A -+ B\nA !> B")

    def test_disagreeing_edges_ignored(self):
        dm = dotmotif.dotmotif(validate=False)
        dm.from_motif("A -+ B\nA !> B")
