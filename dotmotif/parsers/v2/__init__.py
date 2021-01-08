#!/usr/bin/env python3

from typing import List
from lark import Lark, Transformer
import networkx as nx
import os

from ...utils import untype_string
from .. import Parser
from ...validators import Validator


dm_parser = Lark(open(os.path.join(os.path.dirname(__file__), "grammar.lark"), "r"))


class DotMotifTransformer(Transformer):
    """
    This transformer converts a parsed Lark tree into a networkx.MultiGraph.
    """

    def __init__(self, validators: List[Validator] = None, *args, **kwargs) -> None:
        self.validators = validators if validators else []
        self.macros: dict = {}
        self.G = nx.MultiDiGraph()
        self.edge_constraints: dict = {}
        self.node_constraints: dict = {}
        self.dynamic_edge_constraints: dict = {}
        self.dynamic_node_constraints: dict = {}
        self.automorphisms: list = []
        super().__init__(*args, **kwargs)

    def transform(self, tree):
        self._transform_tree(tree)
        return (
            self.G,
            self.edge_constraints,
            self.node_constraints,
            self.dynamic_edge_constraints,
            self.dynamic_node_constraints,
            self.automorphisms,
        )

    def edge_clauses(self, tup):
        attrs = {}
        for key, op, val in tup:
            if key not in attrs:
                attrs[key] = {}
            if op not in attrs[key]:
                attrs[key][op] = []
            attrs[key][op].append(val)
        return attrs

    def edge_clause(self, tup):
        key, op, val = tup
        val = untype_string(val)
        return str(key), str(op), val

    def node_constraint(self, tup):

        if len(tup) == 4:
            # This is of the form "Node.Key [OP] Value"
            node_id, key, op, val = tup
            node_id = str(node_id)
            key = str(key)
            op = str(op)
            val = untype_string(val)
            if node_id not in self.node_constraints:
                self.node_constraints[node_id] = {}
            if key not in self.node_constraints[node_id]:
                self.node_constraints[node_id][key] = {}
            if op not in self.node_constraints[node_id][key]:
                self.node_constraints[node_id][key][op] = []
            self.node_constraints[node_id][key][op].append(val)

        elif len(tup) == 5:
            # This is of the form "ThisNode.Key [OP] ThatNode.Key"
            this_node_id, this_key, op, that_node_id, that_key = tup

            this_node_id = str(this_node_id)
            this_key = str(this_key)
            that_node_id = str(that_node_id)
            that_key = str(that_key)
            op = str(op)

            if this_node_id not in self.dynamic_node_constraints:
                self.dynamic_node_constraints[this_node_id] = {}

            if this_key not in self.dynamic_node_constraints[this_node_id]:
                self.dynamic_node_constraints[this_node_id][this_key] = {}
            if op not in self.dynamic_node_constraints[this_node_id][this_key]:
                self.dynamic_node_constraints[this_node_id][this_key][op] = []
            self.dynamic_node_constraints[this_node_id][this_key][op].append(
                (that_node_id, that_key)
            )

        else:
            raise ValueError("Something is wrong with the node comparison", tup)

    def macro_node_constraint(self, tup):

        if len(tup) == 4:
            node_id, key, op, val = tup
            node_id = str(node_id)
            key = str(key)
            op = str(op)
            val = untype_string(val)
            return ("node_constraint", node_id, key, op, val)

        if len(tup) == 5:
            this_node, this_key, op, that_node, that_key = tup
            this_node = str(this_node)
            this_key = str(this_key)
            that_node = str(that_node)
            that_key = str(that_key)
            op = str(op)
            return ("node_constraint", this_node, this_key, op, that_node, that_key)

        raise ValueError(
            "Something is wrong in this macro with the node comparison ", tup
        )

    def key(self, key):
        return str(key)

    def op(self, operator):
        return {
            "=": "==",
            "==": "==",
            ">=": ">=",
            "<=": "<=",
            "<": "<",
            ">": ">",
            "<>": "!=",
            "!=": "!=",
        }[operator]

    def edge(self, tup):
        if len(tup) == 3:
            u, rel, v = tup
            attrs = {}
        elif len(tup) == 4:
            u, rel, v, attrs = tup
        u = str(u)
        v = str(v)
        for val in self.validators:
            val.validate(self.G, u, v, rel["type"], rel["exists"])
        if self.G.has_edge(u, v):
            # There are existing edges. Only add a new one if it's unique
            # from all existing ones.
            candidate_edges = self.G.get_edge_data(u, v)
            # There are many of these because this is a multidigraph.
            for _, edge in candidate_edges.items():
                if edge["exists"] == rel["exists"] and edge["action"] == rel["type"]:
                    # Don't need to re-add an identical edge
                    return
        if (u, v) not in self.edge_constraints:
            self.edge_constraints[(u, v)] = {}
        self.edge_constraints[(u, v)].update(attrs)
        self.G.add_edge(
            u, v, exists=rel["exists"], action=rel["type"], constraints=attrs
        )

    def automorphism_notation(self, tup):
        self.automorphisms.append(tup)

    def relation(self, tup):
        exists, typ = tup
        return {"exists": exists, "type": typ}

    def node_id(self, node_id):
        return str(node_id)

    def variable(self, var):
        return str("".join(str(c) for c in var))

    def rel_exist(self, _):
        return True

    def rel_nexist(self, _):
        return False

    def rel_def(self, _):
        return "SYN"

    def rel_neg(self, _):
        return "INH"

    def rel_pos(self, _):
        return "EXC"

    def iter_op_contains(self, _):
        return "contains"

    def iter_op_in(self, _):
        return "in"

    def iter_op_not_contains(self, _):
        return "!contains"

    def iter_op_not_in(self, _):
        return "!in"

    # Macros
    def macro(self, arg):
        name, args, rules = arg
        self.macros[name] = {"args": args, "rules": rules}

    def arglist(self, args):
        return [str(s) for s in args]

    def edge_macro(self, tup):
        if len(tup) == 3:
            u, rel, v = tup
            attrs = {}
        elif len(tup) == 4:
            u, rel, v, attrs = tup
        # else:
        #     print(tup, len(tup))
        u = str(u)
        v = str(v)
        return (str(u), rel, str(v), attrs)

    def macro_edge_clauses(self, rules):
        return list(rules)

    def macro_rules(self, rules):
        return list(rules)

    def macro_call(self, tup):
        callname, args = tup
        if callname not in self.macros:
            raise ValueError(
                f"Tried to invoke macro '{callname}' but "
                f"macro '{callname}' does not exist."
            )
        macro = self.macros[callname]
        macro_args = macro["args"]
        if isinstance(args, str):
            args = [args]
        if len(macro_args) != len(args):
            raise ValueError(
                f"Tried to invoke macro '{callname}' with "
                f"{len(args)} arguments, but '{callname}' takes "
                f"{len(macro_args)} arguments."
                f"\n"
                f"Called With:     {args}\n"
                f"Macro Arguments: {macro_args}"
            )

        # Else, append the macro to the graph:
        all_rules = []
        for rule in macro["rules"]:
            if isinstance(rule, tuple):
                all_rules.append(rule)
            else:
                for r in rule:
                    all_rules.append(r)

        for rule in all_rules:
            if len(rule) == 3:
                # This is a structural edge with no constraints.
                left, rel, right = rule
                attrs = {}
            elif len(rule) == 4:
                # This is an edge with attributes.
                left, rel, right, attrs = rule
            elif rule[0] == "node_constraint" and len(rule) == 5:
                # This is a node constraint!
                _, node, key, op, val = rule
                node = args[macro_args.index(node)]
                self.node_constraint((node, key, op, val))
                continue
            elif rule[0] == "node_constraint" and len(rule) == 6:
                # This is a dynamic node constraint!
                _, this_node, this_key, op, that_node, that_key = rule
                this_node = args[macro_args.index(this_node)]
                self.node_constraint((this_node, this_key, op, that_node, that_key))
                continue
            # Get the arguments in-place. For example, if left is A,
            # and A is the first arg in macro["args"], then replace
            # all instances of A in the rules with the first arg
            # from the macro call.
            left = str(left)
            right = str(right)
            left = args[macro_args.index(left)]
            right = args[macro_args.index(right)]
            dict_attrs = {}
            for k, v, a in attrs:
                if k not in dict_attrs:
                    dict_attrs[k] = {}
                if v in dict_attrs[k]:
                    dict_attrs[k][v].append(a)
                else:
                    dict_attrs[k][v] = [a]
            self.edge((left, rel, right, dict_attrs))

    def macro_call_re(self, tup):
        callname, args = tup
        if callname not in self.macros:
            raise ValueError(
                f"Tried to invoke macro '{callname}' but "
                f"macro {callname} does not exist."
            )
        macro = self.macros[callname]
        macro_args = macro["args"]
        if len(macro_args) != len(args):
            raise ValueError(
                f"Tried to invoke macro '{callname}' with "
                f"{len(args)} arguments, but {callname} takes "
                f"{len(macro_args)} arguments."
            )
        all_rules = []
        for rule in macro["rules"]:
            if isinstance(rule, tuple):
                all_rules.append(rule)
            else:
                for r in rule:
                    all_rules.append(r)
        return [
            (args[macro_args.index(rule[0])], rule[1], args[macro_args.index(rule[2])])
            for rule in all_rules
        ]


class ParserV2(Parser):
    def __init__(self, validators: List[Validator] = None) -> None:
        if validators is None:
            self.validators: List[Validator] = []
        else:
            self.validators = validators

    def parse(self, dm: str) -> nx.MultiDiGraph:
        """
        """
        G = nx.MultiDiGraph()

        tree = dm_parser.parse(dm)
        (
            G,
            edge_constraints,
            node_constraints,
            dynamic_edge_constraints,
            dynamic_node_constraints,
            automorphisms,
        ) = DotMotifTransformer(validators=self.validators).transform(tree)
        return (
            G,
            edge_constraints,
            node_constraints,
            dynamic_edge_constraints,
            dynamic_node_constraints,
            automorphisms,
        )

