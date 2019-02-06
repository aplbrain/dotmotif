# Node and Edge Constraints

In addition to structural constraints, dotmotif supports attribute constraints. Let's look at a simple example:


## A simple example

```
A -> B
```

This query returns _all_ edges in a graph. Not particularly useful! But look what happens when we add some qualifications:

```
A -> B [weight >= 10]
```

This motif now becomes much more powerful: Only edges with a `weight` attribute value greater than 10 are returned. What if we want a weight within a certain range?

```
A -> B [weight <= 20, weight >= 10]
```

This motif returns all edges with a weight between 10 and 20. What do you think this constraint does?

```
A -> B [weight <= 20, weight >= 10, weight != 12]
```

These examples have looked at edge constraints so far. But motif nodes can have constraints as well!

## Nodes can have constraints as well

Unlike edge operators, which live inside square brackets on the same line as the edge they're describing, node constraints can live anywhere in your motif:

```
A -> B

A.name = "Wilbur"
```

## Some notes on constraint combinations

You can reuse the same constraint operator more than once, like this:

```
A.area < 10
A.area < 20
```

This combination is redundant, and more importantly, it can increase the runtime of your query! When you're dealing with sufficiently large graphs, be sure to design your motifs with runtime in mind.

It is likewise possible (lo! even easy!) to build contradicting constraints:

```
A.name == "Fred"
A.name != "Fred"
```

Even though this seems like a contrived example, it becomes increasingly simple to make this sort of mistake in larger motifs. Though constraint validators will often catch these sorts of mistakes, it's smart to give your motif a once-over before submitting it to run unsuccessfully.

## Everybody now

You can of course run node and edge attributes through the same motif:

```
A -> B [weight >= 0.6]
A.type = "Glu"
B.type = "ACh"
```

# Available Operators

## Edge Operators

| Operator | Notes |
|----------|-------|
| < |
| > |
| <= |
| >= |
| != | OR <> |
| = | OR == |
| in | Edge value is contained within the value specified. For example, `[name in "1234567890"]` will return edges with `name: 1`, `name: 23`, or `name: 6789`. |
| contains | Edge value contains the value specified. For example, `[name contains "GABA"]` will return edges with `name: GABA1`, `name: GABAergic`, or `name: GABALLAMA`. |

## Node Operators

| Operator | Notes |
|----------|-------|
| < |
| > |
| <= |
| >= |
| != | OR <> |
| = | OR == |
| in | Node value is contained within the value specified. For example, `A.name in "1234567890"` will return nodes with `name: 1`, `name: 23`, or `name: 6789`. |
| contains | Node value contains the value specified. For example, `A.name contains "GABA"` will return nodes with `name: GABA1`, `name: GABAergic`, or `name: GABALLAMA`. |
