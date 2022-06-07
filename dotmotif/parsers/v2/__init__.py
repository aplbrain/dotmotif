#!/usr/bin/env python3

from typing import List
import os
import uuid
from lark import Lark, Transformer
import networkx as nx

from ...utils import untype_string
from .. import Parser
from ...validators import Validator


dm_parser = Lark(open(os.path.join(os.path.dirname(__file__), "grammar.lark"), "r"))


def _unquote_string(s):
    """
    Remove quotes from a string.
    """
    if s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    if s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    return s


class DotMotifTransformer(Transformer):
    """
    This transformer converts a parsed Lark tree into a networkx.MultiGraph.
    """

    def __init__(self, validators: List[Validator] = None, *args, **kwargs) -> None:
        self.validators = validators if validators else []
        self.macros: dict = {}
        self.G = nx.MultiDiGraph()
        self._constraints = {}
        self._dynamic_constraints = {}

        self.edge_constraints: dict = {}
        self.node_constraints: dict = {}
        self.dynamic_edge_constraints: dict = {}
        self.dynamic_node_constraints: dict = {}
        self.named_edges: dict = {}
        self.automorphisms: list = []
        super().__init__(*args, **kwargs)

    def transform(self, tree):
        self._transform_tree(tree)

        # Sort _constraints and _dynamic_constraints into edges and nodes.
        # We need to defer this to the very end of transformation because
        # we don't require entities to be introduced in any particular order.

        for entity_id, constraints in self._constraints.items():
            # First check to see if this exists in the graph as a node:
            if entity_id in self.G.nodes:
                # This is a node, and will be sorted into the node_constraints
                if entity_id not in self.node_constraints:
                    self.node_constraints[entity_id] = {}
                for key, ops in constraints.items():
                    if key not in self.node_constraints[entity_id]:
                        self.node_constraints[entity_id][key] = {}
                    for op, values in ops.items():
                        if op not in self.node_constraints[entity_id][key]:
                            self.node_constraints[entity_id][key][op] = []
                        self.node_constraints[entity_id][key][op].extend(values)
            elif entity_id in self.named_edges:
                # This is a named edge:
                (u, v, attrs) = self.named_edges[entity_id]
                if (u, v) not in self.edge_constraints:
                    self.edge_constraints[(u, v)] = {}
                for key, ops in constraints.items():
                    if key not in self.edge_constraints[(u, v)]:
                        self.edge_constraints[(u, v)][key] = {}
                    for op, values in ops.items():
                        if op not in self.edge_constraints[(u, v)][key]:
                            self.edge_constraints[(u, v)][key][op] = []
                        self.edge_constraints[(u, v)][key][op].extend(values)
            else:
                raise KeyError(
                    f"Entity {entity_id} is neither a node nor a named edge in this motif."
                )

        # Now do the same thing for dynamic constraints:
        for entity_id, constraints in self._dynamic_constraints.items():
            # First check to see if this exists in the graph as a node:
            if entity_id in self.G.nodes:
                # This is a node, and will be sorted into the node_constraints
                if entity_id not in self.dynamic_node_constraints:
                    self.dynamic_node_constraints[entity_id] = {}
                for key, ops in constraints.items():
                    if key not in self.dynamic_node_constraints[entity_id]:
                        self.dynamic_node_constraints[entity_id][key] = {}
                    for op, values in ops.items():
                        if op not in self.dynamic_node_constraints[entity_id][key]:
                            self.dynamic_node_constraints[entity_id][key][op] = []
                        self.dynamic_node_constraints[entity_id][key][op].extend(values)

            elif entity_id in self.named_edges:
                # This is a named edge dynamic correspondence:
                (u, v, attrs) = self.named_edges[entity_id]
                if (u, v) not in self.dynamic_edge_constraints:
                    self.dynamic_edge_constraints[(u, v)] = {}
                for key, ops in constraints.items():
                    if key not in self.dynamic_edge_constraints[(u, v)]:
                        self.dynamic_edge_constraints[(u, v)][key] = {}
                    for op, values in ops.items():
                        for value in values:
                            that_edge, that_attr = value
                            tu, tv, _ = self.named_edges[that_edge]
                            if op not in self.dynamic_edge_constraints[(u, v)][key]:
                                self.dynamic_edge_constraints[(u, v)][key][op] = []
                            self.dynamic_edge_constraints[(u, v)][key][op].extend(
                                (tu, tv, that_attr)
                            )
            else:
                raise KeyError(
                    f"Entity {entity_id} is neither a node nor a named edge in this motif."
                )

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
            key = _unquote_string(key)
            op = str(op)
            val = untype_string(val)

            if node_id not in self._constraints:
                self._constraints[node_id] = {}
            if key not in self._constraints[node_id]:
                self._constraints[node_id][key] = {}
            if op not in self._constraints[node_id][key]:
                self._constraints[node_id][key][op] = []
            self._constraints[node_id][key][op].append(val)

        elif len(tup) == 5:
            # This is of the form "ThisNode.Key [OP] ThatNode.Key"
            this_node_id, this_key, op, that_node_id, that_key = tup

            this_node_id = str(this_node_id)
            this_key = str(this_key)
            this_key = _unquote_string(this_key)
            that_node_id = str(that_node_id)
            that_key = str(that_key)
            that_key = _unquote_string(that_key)
            op = str(op)

            if this_node_id not in self._dynamic_constraints:
                self._dynamic_constraints[this_node_id] = {}

            if this_key not in self._dynamic_constraints[this_node_id]:
                self._dynamic_constraints[this_node_id][this_key] = {}
            if op not in self._dynamic_constraints[this_node_id][this_key]:
                self._dynamic_constraints[this_node_id][this_key][op] = []
            self._dynamic_constraints[this_node_id][this_key][op].append(
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
        else:
            raise ValueError(f"Invalid edge definition {tup}")
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

    def named_edge(self, tup):
        if len(tup) == 4:
            u, rel, v, name = tup
            attrs = {}
        elif len(tup) == 5:
            u, rel, v, attrs, name = tup
        else:
            raise ValueError("Something is wrong with the named edge", tup)

        self.named_edges[name] = (u, v, attrs)
        self.edge(tup[:-1])

    def named_edge_macro(self, tup):
        if len(tup) == 4:
            u, rel, v, name = tup
            attrs = {}
        elif len(tup) == 5:
            u, rel, v, attrs, name = tup
        else:
            raise ValueError("Something is wrong with the named edge", tup)

        return ("named_edge", u, rel, v, attrs, name)

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
        else:
            raise ValueError(f"Invalid edge definition {tup} in macro.")
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

        # We will now do two passes through the ruleset. The first pass is to
        # get a list of named edges and simple edges. We will populate the
        # named_edges lookup, and add the plain edges to the motif.
        named_edges = {}
        pending_rules = []
        for rule in all_rules:
            if len(rule) == 3:
                # This is a structural edge with no constraints.
                left, rel, right = rule
                attrs = {}
            elif len(rule) == 4:
                # This is an edge with attributes.
                left, rel, right, attrs = rule
            elif rule[0] == "named_edge":
                # This is a named edge.
                _, left, rel, right, attrs, name = rule
                named_edges[name] = (left, right, attrs)
            else:
                pending_rules.append(rule)
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

        # This is the second pass of the ruleset. Here, we will add constraints
        # to the motif edges and nodes.
        for rule in pending_rules:
            if rule[0] == "node_constraint" and len(rule) == 5:
                # This is a node constraint or a named edge constraint.
                _, name, key, op, val = rule
                # Check to see if name is a named edge.
                if name in named_edges:
                    # This is a simple edge constraint.
                    left, right, named_edge_attrs = named_edges[name]
                    real_left = args[macro_args.index(left)]
                    real_right = args[macro_args.index(right)]
                    # Temporarily add this edge to the motif's named edges,
                    # with a random name.
                    random_name = f"{name}_{str(uuid.uuid4())}"
                    self.named_edges[random_name] = (
                        real_left,
                        real_right,
                        named_edge_attrs,
                    )
                    # "Node.Key [OP] Value"
                    self.node_constraint((random_name, key, op, val))

                else:
                    name = args[macro_args.index(name)]
                    self.node_constraint((name, key, op, val))
                    continue
            elif rule[0] == "node_constraint" and len(rule) == 6:
                # This is a dynamic node constraint or it is a dynamic
                # edge constraint on two named edges.
                _, this_node, this_key, op, that_node, that_key = rule
                if this_node in named_edges:
                    # This is a dynamic edge constraint on two named edges.
                    if that_node not in named_edges:
                        raise ValueError(
                            f"Tried to add dynamic edge constraint on "
                            f"named edge '{this_node}' but named edge "
                            f"'{that_node}' does not exist."
                        )
                    # We will copy similar behavior from the simple case above,
                    # by creating a named edge for the motif and then adding
                    # the constraint to that edge through the node_constraint
                    # method.
                    left, right, named_edge_attrs = named_edges[this_node]
                    real_this_left = args[macro_args.index(left)]
                    real_this_right = args[macro_args.index(right)]
                    random_this_name = f"{this_node}_{str(uuid.uuid4())}"
                    # Now do the same for the that edge:
                    left, right, named_edge_attrs = named_edges[that_node]
                    real_that_left = args[macro_args.index(left)]
                    real_that_right = args[macro_args.index(right)]
                    random_that_name = f"{that_node}_{str(uuid.uuid4())}"
                    # Temporarily add these edges to the motif's named edges,
                    # with random names.
                    self.named_edges[random_this_name] = (
                        real_this_left,
                        real_this_right,
                        named_edge_attrs,
                    )
                    self.named_edges[random_that_name] = (
                        real_that_left,
                        real_that_right,
                        named_edge_attrs,
                    )
                    self.node_constraint(
                        (random_this_name, this_key, op, random_that_name, that_key)
                    )

                else:
                    # This is a dynamic node constraint.
                    this_node = args[macro_args.index(this_node)]
                    self.node_constraint((this_node, this_key, op, that_node, that_key))
                    continue
            else:
                print(self.macros)
                raise ValueError(f"Invalid macro call. Failed on rule: {rule}")

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
        """ """
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
