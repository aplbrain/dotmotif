import dotmotif

import unittest

_THREE_CYCLE = """A -> B\nB -> C\nC -> A\n"""
_THREE_CYCLE_NEG = """A !> B\nB !> C\nC !> A\n"""
_THREE_CYCLE_INH = """A -| B\nB -| C\nC -| A\n"""
_THREE_CYCLE_NEG_INH = """A !| B\nB !| C\nC !| A\n"""

_SEMICOLON_TRIANGLE = """A->B;B->C;C->A"""


class TestDotmotif_Parserv2_DM(unittest.TestCase):
    def test_sanity(self):
        self.assertEqual(1, 1)

    def test_dm_parser(self):
        dm = dotmotif.Motif(_THREE_CYCLE)
        self.assertEqual(len(dm._g.edges()), 3)
        self.assertEqual(len(dm._g.nodes()), 3)

    def test_dm_parser_with_semicolons(self):
        dm = dotmotif.Motif(_SEMICOLON_TRIANGLE)
        self.assertEqual(len(dm._g.edges()), 3)
        self.assertEqual(len(dm._g.nodes()), 3)

    def test_dm_parser_actions(self):
        dm = dotmotif.Motif(_THREE_CYCLE)
        self.assertEqual([e[2]["action"] for e in dm._g.edges(data=True)], ["SYN"] * 3)

        dm = dotmotif.Motif(_THREE_CYCLE_INH)
        self.assertEqual([e[2]["action"] for e in dm._g.edges(data=True)], ["INH"] * 3)

    def test_dm_parser_edge_exists(self):
        dm = dotmotif.Motif(_THREE_CYCLE)
        self.assertEqual([e[2]["exists"] for e in dm._g.edges(data=True)], [True] * 3)

        dm = dotmotif.Motif(_THREE_CYCLE_NEG)
        self.assertEqual([e[2]["exists"] for e in dm._g.edges(data=True)], [False] * 3)

        dm = dotmotif.Motif(_THREE_CYCLE_NEG_INH)
        self.assertEqual([e[2]["exists"] for e in dm._g.edges(data=True)], [False] * 3)

    def test_can_create_variables(self):
        dm = dotmotif.Motif("""A -> B""")
        self.assertEqual(len(dm._g.nodes()), 2)

    def test_can_create_variables_with_underscores(self):
        dm = dotmotif.Motif("""A -> B_""")
        self.assertEqual(len(dm._g.nodes()), 2)

    def test_cannot_create_variables_with_dashes(self):
        with self.assertRaises(Exception):
            dotmotif.Motif("""A -> B-""")

    def test_can_create_variables_with_numbers(self):
        dm = dotmotif.Motif("""A_2 -> B1""")
        self.assertEqual(len(dm._g.nodes()), 2)


class TestDotmotif_Parserv2_DM_Macros(unittest.TestCase):
    def test_macro_not_added(self):
        exp = """\
        edge(A, B) {
            A -> B
        }
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm._g.edges()), 0)

    def test_simple_macro(self):
        exp = """\
        edge(A, B) {
            A -> B
        }
        edge(C, D)
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm._g.edges()), 1)

    def test_simple_macro_construction(self):
        exp = """\
        edge(A, B) {
            A -> B
        }
        edge(C, D)
        """
        dm = dotmotif.Motif(exp)
        exp_edge = list(dm._g.edges(data=True))[0]
        self.assertEqual(exp_edge[0], "C")
        self.assertEqual(exp_edge[1], "D")

    def test_multiline_macro_construction(self):
        exp = """\
        dualedge(A, B) {
            A -> B
            B -> A
        }
        dualedge(C, D)
        """
        dm = dotmotif.Motif(exp)
        exp_edge = list(dm._g.edges(data=True))[0]
        self.assertEqual(exp_edge[0], "C")
        self.assertEqual(exp_edge[1], "D")

    def test_undefined_macro(self):
        exp = """\
        dualedge(A, B) {
            A -> B
            B -> A
        }
        foo(C, D)
        """
        # with self.assertRaises(ValueError):
        with self.assertRaises(Exception):
            dotmotif.Motif(exp)

    def test_wrong_args_macro(self):
        exp = """\
        edge(A, B) {
            A -> B
            B -> A
        }
        edge(C, D, E)
        """
        # with self.assertRaises(ValueError):
        with self.assertRaises(Exception):
            dotmotif.Motif(exp)

    def test_more_complex_macro(self):
        exp = """\
        tri(A, B, C) {
            A -> B
            B -> C
            C -> A
        }
        tri(C, D, E)
        """
        dm = dotmotif.Motif(exp)
        edges = list(dm._g.edges(data=True))
        self.assertEqual(len(edges), 3)

    def test_macro_reuse(self):
        exp = """\
        tri(A, B, C) {
            A -> B
            B -> C
            C -> A
        }
        tri(C, D, E)
        tri(F, G, H)
        """
        dm = dotmotif.Motif(exp)
        edges = list(dm._g.edges(data=True))
        self.assertEqual(len(edges), 6)

    def test_conflicting_macro_invalid_edge_throws(self):
        exp = """\
        tri(A, B, C) {
            A -> B
            B -> C
            C -> A
        }

        nontri(A, B, C) {
            A !> B
            B !> C
            C !> A
        }
        tri(C, D, E)
        nontri(D, E, F)
        """
        # with self.assertRaises(dotmotif.validators.DisagreeingEdgesValidatorError):
        with self.assertRaises(Exception):
            dotmotif.Motif(exp)

    def test_nested_macros(self):
        exp = """\
        dualedge(A, B) {
            A -> B
            B -> A
        }
        dualtri(A, B, C) {
            dualedge(A, B)
            dualedge(B, C)
            dualedge(C, A)
        }
        dualtri(foo, bar, baz)
        """
        dm = dotmotif.Motif(exp)
        edges = list(dm._g.edges(data=True))
        self.assertEqual(len(edges), 6)

    def test_deeply_nested_macros(self):
        exp = """\
        edge(A, B) {
            A -> B
        }
        dualedge(A, B) {
            edge(A, B)
            edge(B, A)
        }
        dualtri(A, B, C) {
            dualedge(A, B)
            dualedge(B, C)
            dualedge(C, A)
        }
        dualtri(foo, bar, baz)
        """
        dm = dotmotif.Motif(exp)
        edges = list(dm._g.edges(data=True))
        self.assertEqual(len(edges), 6)

    def test_clustercuss_macros_no_repeats(self):
        exp = """\
        edge(A, B) {
            A -> B
        }
        dualedge(A, B) {
            edge(A, B)
            edge(B, A)
        }

        dualtri(A, B, C) {
            dualedge(A, B)
            dualedge(B, C)
            dualedge(C, A)
        }

        dualtri(foo, bar, baz)
        dualtri(foo, bar, baf)
        """
        dm = dotmotif.Motif(exp)
        edges = list(dm._g.edges(data=True))
        self.assertEqual(len(edges), 10)

    def test_comment_in_macro(self):
        exp = """\
        # Outside comment
        edge(A, B) {
            # Inside comment
            A -> B
        }
        dualedge(A, B) {
            # Nested-inside comment
            edge(A, B)
            edge(B, A)
        }

        dualedge(foo, bar)
        """
        dm = dotmotif.Motif(exp)
        edges = list(dm._g.edges(data=True))
        self.assertEqual(len(edges), 2)

    def test_combo_macro(self):
        exp = """\
        edge(A, B) {
            A -> B
        }
        dualedge(A, B) {
            # Nested-inside comment!
            edge(A, B)
            B -> A
        }

        dualedge(foo, bar)
        """
        dm = dotmotif.Motif(exp)
        edges = list(dm._g.edges(data=True))
        self.assertEqual(len(edges), 2)

    def test_comment_macro_inline(self):
        exp = """\
        edge(A, B) {
            A -> B
        }
        dualedge(A, B) {
            # Nested-inside comment!
            edge(A, B) # inline comment
            B -> A
        }

        dualedge(foo, bar) # inline comment
        # standalone comment
        foo -> bar # inline comment
        """
        dm = dotmotif.Motif(exp)
        edges = list(dm._g.edges(data=True))
        self.assertEqual(len(edges), 2)

    def test_alphanumeric_variables(self):
        exp = """\
        edge(A, B) {
            A -> B
        }
        dualedge(A1, B) {
            # Nested-inside comment!
            edge(A1, B) # inline comment
            B -> A1
        }

        dualedge(foo_1, bar_2) # inline comment
        # standalone comment
        foo_1 -> bar_2 # inline comment
        """
        dm = dotmotif.Motif(exp)
        edges = list(dm._g.edges(data=True))
        self.assertEqual(len(edges), 2)
        self.assertEqual(list(dm._g.nodes()), ["foo_1", "bar_2"])
        self.assertEqual(type(list(dm._g.nodes())[0]), str)

        new_exp = """
        L1 -> Mi1
        L1 -> Tm3
        L3 -> Mi9
        """
        dm = dotmotif.Motif(new_exp)
        self.assertEqual(list(dm._g.nodes()), ["L1", "Mi1", "Tm3", "L3", "Mi9"])


class TestDotmotif_Parserv2_DM_EdgeAttributes(unittest.TestCase):
    def test_basic_edge_attr(self):
        exp = """\
        Aa -> Ba [type == 1]
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm._g.edges()), 1)
        u, v, d = list(dm._g.edges(["Aa", "Bb"], data=True))[0]
        self.assertEqual(type(list(dm._g.nodes())[0]), str)
        self.assertEqual(type(list(dm._g.nodes())[1]), str)
        self.assertEqual(d["constraints"]["type"], {"==": [1]})

    def test_edge_multi_attr(self):
        exp = """\
        Aa -> Ba [type != 1, type != 12]
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm._g.edges()), 1)
        u, v, d = list(dm._g.edges(data=True))[0]
        self.assertEqual(d["constraints"]["type"], {"!=": [1, 12]})

    def test_edge_macro_attr(self):
        exp = """\
        macro(Aa, Ba) {
            Aa -> Ba [type != 1, type != 12]
        }

        macro(X, Y)
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm._g.edges()), 1)
        u, v, d = list(dm._g.edges(data=True))[0]
        self.assertEqual(d["constraints"]["type"], {"!=": [1, 12]})


class TestDotmotif_Parserv2_DM_NodeAttributes(unittest.TestCase):
    def test_basic_node_attr(self):
        exp = """\
        Aa -> Ba

        Aa.type = "excitatory"
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_node_constraints()), 1)
        self.assertEqual(list(dm.list_node_constraints().keys()), ["Aa"])

    def test_basic_node_attr_bracket_keying(self):
        exp = """\
        Aa -> Ba

        Aa['type'] = "excitatory"
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_node_constraints()), 1)
        self.assertEqual(list(dm.list_node_constraints().keys()), ["Aa"])

    def test_node_multi_attr(self):
        exp = """\
        Aa -> Ba

        Aa.type = "excitatory"
        Aa.size = 4.5
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_node_constraints()), 1)
        self.assertEqual(len(dm.list_node_constraints()["Aa"]), 2)
        self.assertEqual(dm.list_node_constraints()["Aa"]["type"]["="], ["excitatory"])
        self.assertEqual(dm.list_node_constraints()["Aa"]["size"]["="], [4.5])
        self.assertEqual(list(dm.list_node_constraints().keys()), ["Aa"])

    def test_multi_node_attr(self):
        exp = """\
        Aa -> Ba

        Aa.type = "excitatory"
        Ba.size=4.0
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_node_constraints()), 2)
        self.assertEqual(list(dm.list_node_constraints().keys()), ["Aa", "Ba"])

    def test_node_macro_attr(self):
        exp = """\
        macro(A) {
            A.type = "excitatory"
            A.size >= 4.0
        }
        Aaa -> Ba
        macro(Aaa)
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_node_constraints()), 1)
        self.assertEqual(list(dm.list_node_constraints().keys()), ["Aaa"])

        exp = """\
        macro(A) {
            A.type = "excitatory"
            A.size >= 4.0
        }
        Aaa -> Ba
        macro(Aaa)
        macro(Ba)
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_node_constraints()), 2)
        self.assertEqual(list(dm.list_node_constraints().keys()), ["Aaa", "Ba"])


class TestDynamicNodeConstraints(unittest.TestCase):
    def test_dynamic_constraints(self):
        """
        Test that comparisons may be made between variables, e.g.:

        A.type != B.type

        """
        exp = """\
        A -> B
        A.radius < B.radius
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_dynamic_node_constraints()), 1)

    def test_dynamic_constraints_brackets(self):
        """
        Test that comparisons may be made between variables, e.g.:

        A.type != B.type

        """
        exp = """\
        A -> B
        A['radius'] < B["radius"]
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_dynamic_node_constraints()), 1)

    def test_dynamic_constraints_in_macro(self):
        """
        Test that comparisons may be made between variables in a macro, e.g.:

        A.type != B.type

        """
        exp = """\
        macro(A, B) {
            A.radius > B.radius
        }
        macro(A, B)
        A -> B
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_dynamic_node_constraints()), 1)

    def test_dynamic_constraints_bracketed_in_macro(self):
        """
        Test that comparisons may be made between variables in a macro, e.g.:

        A.type != B.type

        """
        exp = """\
        macro(A, B) {
            # A.radius > B.radius
            A["radius"] > B['radius']
        }
        macro(A, B)
        A -> B
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_dynamic_node_constraints()), 1)

    def test_failed_node_lookup(self):
        """
        Test that comparisons may be made between variables, e.g.:

        A.type != B.type

        """
        exp = """\
        A -> B
        C.radius < B.radius
        """
        with self.assertRaises(KeyError):
            dotmotif.Motif(exp)


class TestEdgeAliasConstraints(unittest.TestCase):
    def test_can_create_aliases(self):
        dotmotif.Motif("""A -> B as ab""")
        assert True

    def test_can_create_aliases_with_constraints(self):
        dotmotif.Motif("""A -> B [type != 1] as ab_2""")
        assert True

    def test_can_create_alised_edge_constraints_nondynamic(self):
        dotmotif.Motif(
            """
        A -> B [type != 1] as ab_2
        ab_2.flavor = "excitatory"
        """
        )
        assert True

    def test_can_create_alised_edge_constraints_dynamic(self):
        dotmotif.Motif(
            """
        A -> B [type != 1] as ab_2
        B -> A as ba
        ab_2.flavor = ba.flavor
        """
        )
        assert True

    def test_failed_edge_lookup(self):
        """
        Test that comparisons may be made between variables, e.g.:

        A.type != B.type

        """
        exp = """\
        A -> B as ab
        acb.radius = 3
        """
        with self.assertRaises(KeyError):
            dotmotif.Motif(exp)

    def test_quoted_attribute_edge_constraint(self):
        exp = """\
        A -> B as ab
        ab["flavor"] = "excitatory"
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_edge_constraints()), 1)
        self.assertEqual(
            dm.list_edge_constraints()[("A", "B")]["flavor"]["="], ["excitatory"]
        )

    def test_quoted_attribute_dynamic_edge_constraint(self):
        exp = """\
        A -> B as ab
        B -> A as ba
        ab["flavor"] = ba["flavor"]
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_dynamic_edge_constraints()), 1)
        self.assertEqual(
            dm.list_dynamic_edge_constraints()[("A", "B")]["flavor"]["="],
            ["B", "A", "flavor"],
        )


class TestEdgeConstraintsInMacro(unittest.TestCase):
    def test_simple_edge_constraint_in_macro(self):
        exp = """\
        macro(A, B) {
            A -> B as ab
            ab.radius > 1
        }
        macro(A, B)
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_edge_constraints()), 1)

    def test_dynamic_edge_constraint_in_macro(self):
        exp = """\
        macro(A, B) {
            A -> B as ab
            B -> A as ba
            ab.weight > ba.weight
        }
        macro(A, B)
        """
        dm = dotmotif.Motif(exp)
        self.assertEqual(len(dm.list_dynamic_edge_constraints()), 1)
