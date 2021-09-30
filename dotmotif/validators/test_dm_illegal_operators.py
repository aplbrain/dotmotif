import unittest
import dotmotif


class TestDotmotifIllegal(unittest.TestCase):
    """
    Test illegal dotmotif operations.
    """

    def test_disagreeing_edges(self):
        dm = dotmotif.Motif(
            validators=[dotmotif.validators.DisagreeingEdgesValidator()]
        )
        with self.assertRaises(Exception):
            dm.from_motif("A -> B\nA !> B")

    def test_disagreeing_edges_ignored(self):
        dm = dotmotif.Motif(validators=[])
        dm.from_motif("A -+ B\nA !> B")
