# Automorphisms

DotMotif can be instructed to automatically handle automorphisms or _not_, depending on your use-case. For example, in the following graph:

<img src='https://g.gravizo.com/svg?
 digraph G {
   A -> C;
   B -> C;
 }
'/>

With the following motif:

<img src='https://g.gravizo.com/svg?
 digraph G {
   x -> y
 }
'/>

You may want to get the following results:

| x   | y   |
| --- | --- |
| A   | C   |
| B   | C   |

Or you may wish to only receive _one_ representation of the automorphism set:

| x   | y   |
| --- | --- |
| A*  | C   |

<small>\* Here, A may equally likely be replaced with B.</small>

In order to indicate to DotMotif that you would like one behavior or the other, you can do one of two things:

## Using the `exclude_automorphisms` flag

You can pass the `exclude_automorphisms` flag to the `dotmotif` constructor. The default is `False`: In other words, all automorphisms are included:


### Default Behavior

Graph:
```
A -> B
B -> C
C -> A
```

Motif (the same text):
```
A -> B
B -> C
C -> A
```

Here, `E` is an executor (it does not matter which flavor; let's imagine it's a `NetworkXExecutor`, for example):

```python
>>> motif dotmotif().from_motif("triangle.motif")
>>> len(E.find(motif))
3
```

### With `exclude_automorphisms` set to `True`:

```python
>>> motif dotmotif(exclude_automorphisms=True).from_motif("triangle.motif")
>>> len(E.find(motif))
1
```

## Using the `===` automorphism operator

The `===` operator is the automorphism operator in the DotMotif syntax. You can use it to indicate that two nodes are isomorphic:

```
A -> B
B -> C
C -> A

A === B
B === C
```

In the above example, we indicate that we do not care about the order of triangle nodes. (We do not need to include `A===C` because the DotMotif automorphism operator is transitive and symmetric.)
