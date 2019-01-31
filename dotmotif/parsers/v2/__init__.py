#!/usr/bin/env python3

from typing import List
from lark import Lark, Transformer
import networkx as nx

from ...utils import untype_string
from .. import Parser
from ...validators import Validator


GRAMMAR = """
// See Extended Backus-Naur Form for more details.
start: comment_or_block+



// Contents may be either comment or block.
comment_or_block: block

// Comments are signified by a hash followed by anything. Any line that follows
// a comment hash is thrown away.

?comment        : "#" COMMENT

// A block may consist of either an edge ("A -> B") or a "macro", which is
// essentially an alias capability.
block           : edge
                | macro
                | macro_call
                | node_constraint
                | comment




// A macro can be considered a "function" definition that can be used in the
// rest of the file to define complex structure. For example,
//     foo(a, b) { a -> b }; foo(A, B);
// is the same as:
//     A -> B
// While this is a simple case, this is an immensely powerful tool.
macro           : variable "(" arglist ")" "{" macro_rules "}"

// A series of arguments to a macro
?arglist        : variable ("," variable)*

macro_rules     : macro_block+

?macro_block    : edge_macro
                | macro_call_re
                | comment

// A "hypothetical" edge that forms a subgraph structure.
edge_macro      : node_id relation node_id




// A macro is called like a function: foo(args).
macro_call      : variable "(" arglist ")"
?macro_call_re  : variable "(" arglist ")"




// Edges are currently composed of a node, a relation, and a node. In other
// words, an arbitrary word, a relation between them, and then another node.
// Edges can also have optional edge attributes, delimited from the original
// structure with square brackets.
edge            : node_id relation node_id
                | node_id relation node_id "[" edge_clauses "]"

// A Node ID is any contiguous (that is, no whitespace) word.
?node_id        : variable

// A relation is a bipartite: The first character is an indication of whether
// the relation exists or not. The following characters indicate if a relation
// has a type other than the default, positive, and negative types offered
// by default.
relation        : relation_exist relation_type

// A "-" means the relation exists; "~" means the relation does not exist.
relation_exist  : "-"                               -> rel_exist
                | "~"                               -> rel_nexist
                | "!"                               -> rel_nexist

// The valid types of relation are single-character, except for the custom
// relation type which is user-defined and lives inside square brackets.
relation_type   : ">"                               -> rel_def
                | "+"                               -> rel_pos
                | "-"                               -> rel_neg
                | "|"                               -> rel_neg

// Edge attributes are separated from the main edge declaration with sqbrackets
edge_clauses   : edge_clause ("," edge_clause)*

?edge_clause     : key op value


// Node constraints:
node_constraint : node_id "." key op value
                | node_id "." key op "\\"" value "\\""



?key            : WORD
?value          : WORD | NUMBER
?op             : OPERATOR


?variable       : (WORD | VAR_SEP | NUMBER)+

OPERATOR        : /[\=\>\<\!]?[\=]/
VAR_SEP         : /[\_\-]/
COMMENT         : /\#[^\\n]+/
%ignore COMMENT

%import common.WORD
%import common.SIGNED_NUMBER  -> NUMBER
%import common.WS
%ignore WS
"""


dm_parser = Lark(GRAMMAR)


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
        super().__init__(*args, **kwargs)

    def transform(self, tree):
        self._transform_tree(tree)
        return self.G, self.edge_constraints, self.node_constraints

    def edge_clauses(self, tup):
        attrs = {}
        for key, op, val in tup:
            if key not in attrs:
                attrs[key] = {}
            attrs[key][op] = val
        return attrs

    def edge_clause(self, tup):
        key, op, val = tup
        try:
            val = float(val)
        except:
            val = str(val)
        return str(key), str(op), val

    def key(self, key):
        return key

    def value(self, value):
        return value

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
            for i, edge in candidate_edges.items():
                if edge["exists"] == rel["exists"] and edge["action"] == rel["type"]:
                    # Don't need to re-add an identical edge
                    return
        if (u, v) not in self.edge_constraints:
            self.edge_constraints[(u, v)] = {}
        self.edge_constraints[(u, v)].update(attrs)
        self.G.add_edge(
            u, v, exists=rel["exists"], action=rel["type"], constraints=attrs
        )

    def relation(self, tup):
        exists, type = tup
        return {"exists": exists, "type": type}

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

    # Macros
    def macro(self, arg):
        name, args, rules = arg
        self.macros[name] = {"args": args, "rules": rules}

    def arglist(self, args):
        return [str(s) for s in args]

    def edge_macro(self, tup):
        u, rel, v = tup
        return (str(u), rel, str(v))

    def macro_rules(self, rules):
        return list(rules)

    def macro_call(self, tup):
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

        # Else, append the macro to the graph:
        all_rules = []
        for rule in macro["rules"]:
            if isinstance(rule, tuple):
                all_rules.append(rule)
            else:
                for r in rule:
                    all_rules.append(r)

        for rule in all_rules:
            # Get the arguments in-place. For example, if left is A,
            # and A is the first arg in macro["args"], then replace
            # all instances of A in the rules with the first arg
            # from the macro call.
            left, rel, right = rule
            left = args[macro_args.index(left)]
            right = args[macro_args.index(right)]
            self.edge((left, rel, right))

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
        G, edge_constraints, node_constraints = DotMotifTransformer(
            validators=self.validators
        ).transform(tree)
        return G, edge_constraints, node_constraints
