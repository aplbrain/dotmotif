# Getting started with dotmotif

Once you have [installed `dotmotif`](#), you can start writing queries.

Queries can be written in one of two languages;

* CSV, the conventional edge-list format
* .motif, the task-specific motif-finding language designed for use with `dotmotif`

For this tutorial, we will be using the .motif format, but you can follow the instructions [here](#) for CSV instructions.

# 1. Write your motif

First, let's write the motif we want to find. The .motif format uses a handful of simple notational primitives that you can combine to form more complex network structures.

To illustrate this, let's start with a simple 4-cycle. We'll name the nodes `A`, `B`, `C`, and `D`, but you can name them anything you want, as long as you only use alphanumeric characters (uppercase, lowercase, and numbers).

```
A -- B
B -- C
C -- D
D -- A
```

Easy enough!

# 2. Refine the motif

Let's add some more complex structure. Let's say we want to _disallow_ diagonal connections between non-neighboring nodes. Let's add that to our file:

```
# Basic structure
A -- B
B -- C
C -- D
D -- A

# Disallow diagonals:
A !- C
C !- A
B !- D
D !- B
```

We've introduced a few new concepts here, so let's break down the new syntax. First, note that lines starting with `#` are ignored by the compiler, so you can add comments to your .motif files.

Next, see that we indicated a _synapse_ with the `--` notation. The first component can be negated using the `!` operator to tell the compiler that we want to _prohibit_ that edge.
