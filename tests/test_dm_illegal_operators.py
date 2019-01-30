import unittest
import dotmotif


class TestDotmotifIllegal(unittest.TestCase):
    """
    Test illegal dotmotif operations.
    """

    # def test_disagreeing_edges(self):
    #     dm = dotmotif.dotmotif(
    #         validators=[
    #             dotmotif.validators.DisagreeingEdgesValidator
    #         ]
    #     )
    #     with self.assertRaises(
    #         dotmotif.validators.DisagreeingEdgesValidatorError
    #     ):
    #         dm.from_motif("A -- B\nA !- B")

    def test_disagreeing_edges_ignored(self):
        dm = dotmotif.dotmotif(validators=[])
        dm.from_motif("A -+ B\nA !> B")

    # def test_cells_enforce_monotypy(self):
    #     dm = dotmotif.dotmotif(enforce_monotypy=True)
    #     with self.assertRaises(dotmotif.MotifError):
    #         dm.from_motif("A -> B\nA -| B")

    # def test_cells_enforce_monotypy_ignored(self):
    #     dm = dotmotif.dotmotif(enforce_monotypy=False)
    #         dm.from_motif("A -> B\nA -| B")
