from . import ParserV2
import dotmotif

import unittest

_THREE_CYCLE = """A -> B\nB -> C\nC -> A\n"""
_THREE_CYCLE_NEG = """A !> B\nB !> C\nC !> A\n"""
_THREE_CYCLE_INH = """A -| B\nB -| C\nC -| A\n"""
_THREE_CYCLE_NEG_INH = """A !| B\nB !| C\nC !| A\n"""
_ABC_TO_D = """\nA -> D\nB -> D\nC -> D\n"""

_THREE_CYCLE_CSV = """\nA,B\nB,C\nC,A\n"""
_THREE_CYCLE_NEG_CSV = """\nA,B\nB,C\nC,A\n"""


class TestDotmotif_Parserv2_DM(unittest.TestCase):

    def test_sanity(self):
        self.assertEqual(1, 1)

    def test_dm_parser(self):
        dm = dotmotif.dotmotif(parser=ParserV2)
        dm.from_motif(_THREE_CYCLE)
        self.assertEqual(len(dm._g.edges()), 3)
        self.assertEqual(len(dm._g.nodes()), 3)

    def test_dm_parser_actions(self):
        dm = dotmotif.dotmotif(parser=ParserV2)
        dm.from_motif(_THREE_CYCLE)
        self.assertEqual([
            e[2]['action']
            for e in dm._g.edges(data=True)
        ], ['SYN'] * 3)

        dm = dotmotif.dotmotif(parser=ParserV2)
        dm.from_motif(_THREE_CYCLE_INH)
        self.assertEqual([
            e[2]['action']
            for e in dm._g.edges(data=True)
        ], ['INH'] * 3)

    def test_dm_parser_edge_exists(self):
        dm = dotmotif.dotmotif(parser=ParserV2)
        dm.from_motif(_THREE_CYCLE)
        self.assertEqual([
            e[2]['exists']
            for e in dm._g.edges(data=True)
        ], [True] * 3)

        dm = dotmotif.dotmotif(parser=ParserV2)
        dm.from_motif(_THREE_CYCLE_NEG)
        self.assertEqual([
            e[2]['exists']
            for e in dm._g.edges(data=True)
        ], [False] * 3)

        dm = dotmotif.dotmotif(parser=ParserV2)
        dm.from_motif(_THREE_CYCLE_NEG_INH)
        self.assertEqual([
            e[2]['exists']
            for e in dm._g.edges(data=True)
        ], [False] * 3)


class TestDotmotif_Parserv2_DM_Macros(unittest.TestCase):

    def test_macro_not_added(self):
        exp = """\
        edge(A, B) {
            A -> B
        }
        """
        dm = dotmotif.dotmotif(parser=ParserV2)
        dm.from_motif(exp)
        self.assertEqual(len(dm._g.edges()), 0)

    def test_simple_macro(self):
        exp = """\
        edge(A, B) {
            A -> B
        }
        edge(C, D)
        """
        # dm = dotmotif.dotmotif(parser=ParserV2)
        # dm.from_motif(exp)
        # self.assertEqual(len(dm._g.edges()), 1)

    def test_simple_macro_construction(self):
        exp = """\
        edge(A, B) {
            A -> B
        }
        edge(C, D)
        """
        dm = dotmotif.dotmotif(parser=ParserV2)
        dm.from_motif(exp)
        # exp_edge = list(dm._g.edges(data=True))[0]
        # self.assertEqual(exp_edge[0], "C")
        # self.assertEqual(exp_edge[1], "D")

    def test_multiline_macro_construction(self):
        exp = """\
        dualedge(A, B) {
            A -> B
            B -> A
        }
        dualedge(C, D)
        """
        dm = dotmotif.dotmotif(parser=ParserV2)
        dm.from_motif(exp)
        # exp_edge = list(dm._g.edges(data=True))[0]
        # self.assertEqual(exp_edge[0], "C")
        # self.assertEqual(exp_edge[1], "D")

    def test_undefined_macro(self):
        exp = """\
        dualedge(A, B) {
            A -> B
            B -> A
        }
        foo(C, D)
        """
        with self.assertRaises(ValueError):
            dm = dotmotif.dotmotif(parser=ParserV2)
            dm.from_motif(exp)

    def test_undefined_macro(self):
        exp = """\
        edge(A, B) {
            A -> B
            B -> A
        }
        edge(C, D, E)
        """
        with self.assertRaises(ValueError):
            dm = dotmotif.dotmotif(parser=ParserV2)
            dm.from_motif(exp)
