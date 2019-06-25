# Latest Version

See [Language-Spec.md](Language-Spec.md) for more details.

## Older versions

### v2.0

```
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
                | comment




// A macro can be considered a "function" definition that can be used in the
// rest of the file to define complex structure. For example,
//     foo(a, b) { a -> b }; foo(A, B);
// is the same as:
//     A -> B
// While this is a simple case, this is an immensely powerful tool.
macro           : word "(" arglist ")" "{" macro_rules "}"

// A series of arguments to a macro
?arglist        : word ("," word)*

macro_rules     : macro_block+

?macro_block    : edge_macro
                | macro_call_re
                | comment

// A "hypothetical" edge that forms a subgraph structure.
edge_macro      : node_id relation node_id




// A macro is called like a function: foo(args).
macro_call      : word "(" arglist ")"
?macro_call_re  : word "(" arglist ")"




// Edges are currently composed of a node, a relation, and a node. In other
// words, an arbitrary word, a relation between them, and then another node.
edge            : node_id relation node_id

// A Node ID is any contiguous (that is, no whitespace) word.
?node_id        : word

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


?word           : WORD


COMMENT         : /\#[^\\n]+/
%ignore COMMENT

%import common.WORD
%import common.SIGNED_NUMBER  -> NUMBER
%import common.WS
%ignore WS
```

For example, the following two lines may be considered to be the same:

```
A -> B
A -[SYN] B
```

Likewise, bracket-form is equivalent to inline type aliases:

```
C !+ D
C ![EXCITES] D
```

## Macros

Macros enable simple motif construction from simpler subcomponents:

```dotmotif
# Nodes that are connected in only one direction:
unidirectional(n, m) {
    n -> m
    m ~> n
}

# All triangles for which edges exist in only one direction:
unidirectionalTriangle(x, y, z) {
    unidirectional(x, y)
    unidirectional(y, z)
    unidirectional(z, x)
}

unidirectionalTriangle(A, B, C)
unidirectionalTriangle(C, D, E)
```

## v1.0 (October 23, 2018)

```
S -> T
T -> nERn   | TDT | c  | ε
R -> >      | +   | ~  | ?
E -> -      | !   | ?
D -> ;      | \n
n -> /\S+/
c -> /\#.*/
```

For example, the following notates that nodes `α`, `β`, and `γ` form a triangle:

```
α -> β
β -> γ
γ -> α
```

This example demonstrates that `α`, `β`, `γ`, and `λ` form a directed 4-cycle with no diagonals:

```
# Directed 4-cycle:
α -> β
β -> γ
γ -> λ
λ -> α

# No diagonals:
α !> γ
γ !> α
β !> λ
λ !> β
```

Note that comments, prefixed with a `#` character, are valid syntax.
