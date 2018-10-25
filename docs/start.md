# Getting started with dotmotif

Once you have [installed `dotmotif`](#), you can start writing queries.

Queries are written in `.motif` syntax, the task-specific motif-finding language designed for use with `dotmotif`.


# 1. Write your motif

First, let's write the motif we want to find. The .motif format uses a handful of simple notational primitives that you can combine to form more complex network structures.

To illustrate this, let's start with a simple 4-cycle. We'll name the nodes `A`, `B`, `C`, and `D`, but you can name them anything you want, as long as you only use alphanumeric characters (uppercase, lowercase, and numbers).

```
A -> B
B -> C
C -> D
D -> A
```

Easy enough!

# 2. Refine the motif

Let's add some more complex structure. Let's say we want to _disallow_ diagonal connections between non-neighboring nodes. Let's add that to our file:

```
# Basic structure
A -> B
B -> C
C -> D
D -> A

# Disallow diagonals:
A !> C
C !> A
B !> D
D !> B
```

We've introduced a few new concepts here, so let's break down the new syntax. First, note that lines starting with `#` are ignored by the compiler, so you can add comments to your .motif files.

Next, see that we indicated a _synapse_ with the `->` notation. The first component can be negated using the `!` operator to tell the compiler that we want to _prohibit_ that edge. If you do not prohibit an edge, your search results may include places where those nodes have OR do not have an edge.

# 3. Refactor the motif

You can use dotmotif "macros" to simplify the process of writing a motif. You can think of macros as a type of template that enables you to write a pattern once and then reuse it (like a function in other languages). This reduces the possibility of typos, and also enables you to write more complex structures without confusion.

Let's say we want to find three triangles where edges connect in one direction (say, clockwise), but not in the other direction.

We can either write this as:

```
# Triangle 1
A -> B
B !> A
B -> C
C !> B
C -> A
A !> C

# Triangle 2
D -> E
E !> D
E -> F
F !> E
F -> D
D !> F

# Triangle 2
G -> A
A !> D
A -> F
F !> A
F -> D
D !> F
```

(18 lines)

Or we can use a macro:

```
# One-direction triangle
unitriangle(x, y, z) {
    x -> y
    y !> x
    y -> z
    z !> y
    z -> x
    x !> z
}

unitriangle(A, B, C)
unitriangle(D, E, F)
unitriangle(G, A, D)
```

(11 lines)

The astute may notice that we can simplify this even further:

```
# One-direction edge
uniedge(n, m) {
    n -> m
    m !> n
}

# One-direction triangle
unitriangle(x, y, z) {
    uniedge(x, y)
    uniedge(y, z)
    uniedge(z, x)
}

unitriangle(A, B, C)
unitriangle(D, E, F)
unitriangle(G, A, D)
```

(11 lines)

This last example is _very_ readable, and far more tractable than trying to understand 18 lines of individual rules!

# Validation

Let's try another example.

`impossible.motif`
```
# One-direction edge
uniedge(n, m) {
    n -> m
    m !> n
}

unitriangle(x, y, z) {
    uniedge(x, y)
    uniedge(y, z)
    uniedge(z, x)
}

unitriangle(A, B, C)
unitriangle(C, B, A)
```

If you're paying attention, you'll notice right away that something is wrong here: There's no way that a `unitriangle` can exist between `ABC` _and_ `CBA` simultaneously. This is still perfectly valid dotmotif _syntax_, but the motif itself is impossible.

Luckily, the dotmotif Python package will complain when you try to compile this:

```python
from dotmotif import dotmotif

dotmotif().from_motif('impossible.motif')
```

```python
'DisagreeingEdgesValidatorError: Trying to add <C-B exists=True> but <C-B exists=False> already in motif.'
```

This compile-time error will save you tons of time because dotmotif will warn you ahead of time that the motif cannot possibly exist in your haystack graph. If you want to deliberately ignore this issue and still send this query for searching, you can specify a list of `validators` in your dotmotif instantiation:

```python
dotmotif.dotmotif(validators=[]).from_motif(m)
```

This empty list overrides the default list of validators, which includes a built-in `DisagreeingEdgesValidator`. It's not recommended that you do this — but it is _possible_.
