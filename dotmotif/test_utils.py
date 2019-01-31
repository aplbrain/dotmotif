from unittest import TestCase

from .utils import untype_string

class TestConverter(TestCase):

    def test_untype_string_float(self):
        self.assertEqual(
            untype_string("3.14"),
            3.14
        )
        self.assertEqual(
            untype_string("-.14"),
            -0.14
        )
    def test_untype_string_int(self):
        self.assertEqual(
            untype_string("3"),
            3
        )
        self.assertEqual(
            untype_string("0.0"),
            0
        )

    def test_untype_string_string(self):

        self.assertEqual(
            untype_string("3.5.5"),
            "3.5.5"
        )
