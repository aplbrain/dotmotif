#!/usr/bin/env python3

from typing import List
from lark import Lark, Transformer
import networkx as nx

from .. import Parser
from ...validators import Validator


GRAMMAR = """
// See Extended Backus-Naur Form for more details.
start: comment_or_block+



// Contents may be either comment or block.
comment_or_block: comment
                | block

// Comments are signified by a hash followed by anything. Any line that follows
// a comment hash is thrown away.
comment         : "#" word*

// A block may consist of either an edge ("A -> B") or a "macro", which is
// essentially an alias capability.
block           : edge
                | macro
                | macro_call




// A macro can be considered a "function" definition that can be used in the
// rest of the file to define complex structure. For example,
//     foo(a, b) { a -> b }; foo(A, B);
// is the same as:
//     A -> B
// While this is a simple case, this is an immensely powerful tool.
macro           : word "(" arglist ")" "{" edge_macro+ "}"

// A series of arguments to a macro
arglist         : word ("," word)*

// A "hypothetical" edge that forms a subgraph structure.
edge_macro      : node_id relation node_id




macro_call      : word "(" arglist ")"




// Edges are currently composed of a node, a relation, and a node. In other
// words, an arbitrary word, a relation between them, and then another node.
edge            : node_id relation node_id

// A Node ID is any contiguous (that is, no whitespace) word.
?node_id         : word

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
                | "[" word "]"                      -> rel_typ


?word            : WORD


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
        self.G = nx.MultiDiGraph()
        super().__init__(*args, **kwargs)

    def comment(self, words):
        pass

    def edge(self, tup):
        u, rel, v = tup
        for val in self.validators:
            val.validate(self.G, u, v, rel["type"], rel["exists"])
        self.G.add_edge(u, v, exists=rel["exists"], action=rel["type"])

    def relation(self, tup):
        exists, type = tup
        return {
            "exists": exists,
            "type": type,
        }

    def node_id(self, node_id):
        return node_id

    def word(self, word):
        return str(word)

    def transform(self, tree):
        self._transform_tree(tree)
        return self.G


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
        G = DotMotifTransformer(validators=self.validators).transform(tree)


        # for line in dm.split('\n'):
        #     res = self._parse_dm_line(line.strip())
        #     if res:
        #         u, v, action, exists = res
        #         for val in self.validators:
        #             val.validate(G, u, v, action, exists)
        #         G.add_edge(u, v, exists=exists, action=action)
        return G

    def _parse_dm_line(self, _line: str):
        _line = _line.strip()
        # Tokenize:
        if len(_line) and _line.startswith("#"):
            return None
        line = [t for t in _line.split() if len(t)]
        if len(line) is 0:
            return None

        # Format should be [NEURON_ID, ACTION, NEURON_ID]
        try:
            u, action, v = line
        except ValueError:
            raise ValueError(
                "Line must be of the form [NEURON_ID, ACTION, NEURON_ID], but got {}.".format(
                    line)
            )
        edge_exists = (action[0] != "!")

        return (
            u, v,
            self.ACTIONS[action[-1]],
            edge_exists
        )
