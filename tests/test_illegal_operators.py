import unittest
import dotmotif


class TestDotmotifIllegal(unittest.TestCase):
    """
    Test illegal dotmotif operations.
    """

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

    def test_cells_enforce_monotypy(self):
        dm = dotmotif.dotmotif(enforce_monotypy=True)
        dm.from_motif("A -> B\nA -| B")

    def test_cells_enforce_monotypy_ignored(self):
        dm = dotmotif.dotmotif(enforce_monotypy=True)
        with self.assertRaises(dotmotif.MotifError):
            dm.from_motif("A -> B\nA -| B")
