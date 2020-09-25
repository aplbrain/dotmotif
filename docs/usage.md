# Usage

## Writing a motif

You can currently write motifs in one of two languages; either CSV (in edge-list notation), or dotmotif form, which provides extra specificity when searching a graph (such as synapse polarity).

The following two files are equivalent:

`threecycle.csv`
```
A,B
B,C
C,A
```

`threecycle.motif`
```
# A excites B
A -+ B
# B inhibits C
B -~ C
# We do not know how C influences A
C -? A
```

## Ingesting the motif into dotmotif

```python
from dotmotif import dotmotif

dm = dotmotif().from_csv("threecycle.csv")

# or:
dm = dotmotif().from_motif("threecycle.motif")
```

You can also pass optional parameters into the constructor for the `dotmotif` object. Those arguments are:



## Generating the Query

This will return a string query:

```python
dm.to_cypher() # "MATCH (A:Node)-[:SYN]-> ..."
```

You can chain the entire operation into one single command using the chaining functionality of this library:

```python
dm = dotmotif().from_motif("threecycle.motif").to_cypher()
```

Learn more about motif constraints [here](attributes.md).
