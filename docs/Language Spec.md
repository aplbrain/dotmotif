# v1.0 (October 23, 2018)

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


# v2.0 (Under Development)

```
S -> T                                  # Start
T -> R       | TDT   | TDT   | c | ε    # Term, multiple terms, comment, or empty
R -> nERn    | nERnK                    # v1.0 term, or conditioned (K) term
K -> wV                                 # A 'where' (:) followed by one or more conditions
V -> V       | VdV    | nEEn            # One or more key-value clauses (i.e. "foo=bar")
R -> >       | +      | ~    | ? | B    # Edge type
B -> /\[n\]/                            # Edge type in bracket-form
E -> -       | !      | ?    | G        # Existance or equality
G -> Q       | Qg                       # Comparison
Q -> =       | ε                        # Equality test
g -> <>      | !      | >    | < | =    # Comparator tests
D -> d       | \n                       # Term delimiter
d -> ;                                  # Semicolon delimiter
w -> :                                  # Condition prefix
n -> /\S+/                              # Non-space unicode
c -> /\#.*/                             # Comment-form
```

For example, the following two lines may be considered to be the same:

```
A -> B
A -[SYN] B
```

As may these:

```
A -> B : A.type='inhibitory'; B.type='excitatory'
A -> B : B.type='excitatory'; A.type='inhibitory'
```

Conditions may also be set on the edge's attributes. The `-` character aliases the edge entity.

```
A -> B : -.weight>=0.5; -.weight<=1.0
```

Likewise, bracket-form is equivalent to inline type aliases:

```
C !+ D
C ![EXCITES] D
```
