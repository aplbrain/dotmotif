from unittest import TestCase
import networkx as nx
from ..utils import untype_string
from .. import dotmotif
from tempfile import NamedTemporaryFile


class TestConverter(TestCase):
    def test_untype_string_float(self):
        self.assertEqual(untype_string("3.14"), 3.14)
        self.assertEqual(untype_string("-.14"), -0.14)

    def test_untype_string_int(self):
        self.assertEqual(untype_string("3"), 3)
        self.assertEqual(untype_string("0.0"), 0)

    def test_untype_string_string(self):

        self.assertEqual(untype_string("3.5.5"), "3.5.5")


class TestSaveLoad(TestCase):
    def test_saveload(self):
        m = dotmotif().from_motif(
            """
        A -> B [type=6]
        """
        )
        tf = NamedTemporaryFile()
        m.save(tf)
        tf.flush()
        f = dotmotif.load(tf.name)
        self.assertTrue(nx.is_isomorphic(m._g, f._g))
        self.assertEqual(m.list_edge_constraints(), f.list_edge_constraints())
        self.assertEqual(m.list_node_constraints(), f.list_node_constraints())
        self.assertEqual(m.ignore_direction, f.ignore_direction)
        self.assertEqual(m.limit, f.limit)
        self.assertEqual(m.enforce_inequality, f.enforce_inequality)
        self.assertEqual(m.pretty_print, f.pretty_print)
        tf.close()
