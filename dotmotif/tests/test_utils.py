from unittest import TestCase
import networkx as nx
from ..utils import untype_string, _hashed_dict
from .. import Motif
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
        m = Motif().from_motif(
            """
        A -> B [type=6]
        """
        )
        tf = NamedTemporaryFile()
        m.save(tf)
        tf.flush()
        f = Motif.load(tf.name)
        self.assertTrue(nx.is_isomorphic(m._g, f._g))
        self.assertEqual(m.list_edge_constraints(), f.list_edge_constraints())
        self.assertEqual(m.list_node_constraints(), f.list_node_constraints())
        self.assertEqual(m.ignore_direction, f.ignore_direction)
        self.assertEqual(m.limit, f.limit)
        self.assertEqual(m.enforce_inequality, f.enforce_inequality)
        self.assertEqual(m.pretty_print, f.pretty_print)
        tf.close()


class TestHashColor(TestCase):
    def test_hash_color(self):
        assert _hashed_dict({}) == "#00babe"
        assert _hashed_dict({"a": 1}) != "#00babe"

    def test_order_invariant(self):
        assert _hashed_dict({"a": 1}) == _hashed_dict({"a": 1})
        assert _hashed_dict({"a": 1, "b": 2}) == _hashed_dict({"b": 2, "a": 1})
        assert _hashed_dict({"a": 1, "b": 2}) != _hashed_dict({"b": 2, "a": 2})
        assert _hashed_dict({"a": 1, "b": 2}) != _hashed_dict({"b": 2, "a": 1, "c": 3})
