from unittest import TestCase
import networkx as nx
from ..utils import _deep_merge_constraint_dicts, untype_string, _hashed_dict
from .. import Motif
from tempfile import NamedTemporaryFile
from io import BytesIO
from pathlib import Path


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

    def test_caller_owned_streams_remain_open(self):
        motif = Motif("A -> B")
        stream = BytesIO()

        motif.save(stream)
        stream.seek(0)
        loaded = Motif.load(stream)

        self.assertFalse(stream.closed)
        self.assertTrue(nx.is_isomorphic(motif.to_nx(), loaded.to_nx()))

    def test_pathlike_save_and_load(self):
        motif = Motif("A -> B")
        with NamedTemporaryFile() as temporary_file:
            path = Path(temporary_file.name)
            motif.save(path)
            loaded = Motif.load(path)

        self.assertTrue(nx.is_isomorphic(motif.to_nx(), loaded.to_nx()))


class TestHashColor(TestCase):
    def test_hash_color(self):
        assert _hashed_dict({}) == "#00babe"
        assert _hashed_dict({"a": 1}) != "#00babe"

    def test_order_invariant(self):
        assert _hashed_dict({"a": 1}) == _hashed_dict({"a": 1})
        assert _hashed_dict({"a": 1, "b": 2}) == _hashed_dict({"b": 2, "a": 1})
        assert _hashed_dict({"a": 1, "b": 2}) != _hashed_dict({"b": 2, "a": 2})
        assert _hashed_dict({"a": 1, "b": 2}) != _hashed_dict({"b": 2, "a": 1, "c": 3})


class TestMergeConstraints(TestCase):
    def test_merging_constraints(self):
        assert _deep_merge_constraint_dicts(
            {
                "a": {"b": [1], "c": [2]},
            },
            {
                "a": {"b": [3], "d": [4]},
            },
        ) == {
            "a": {"b": [1, 3], "c": [2], "d": [4]},
        }
