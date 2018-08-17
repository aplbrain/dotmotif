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

| Argument | Type, Default | Behavior |
|----------|------|----------|
`ignore_direction` | `bool`: `False` | Whether to disregard direction when generating the database query |
| `limit` | `int`: `None` | A limit (if any) to impose on the query results |
| `enforce_inequality` | `bool`: `False` | Whether to enforce inequality; in other words, whether two nodes should be permitted to be aliases for the same node. For example, A>B>C; if A!=C, then set to True |

## Generating the Query

This will return a string query:

```python
dm.to_cypher() # "MATCH (A:Neuron)-[:SYN]-> ..."
```

You can chain the entire operation into one single command using the chaining functionality of this library:

```python
dm = dotmotif().from_motif("threecycle.motif").to_cypher()
```

----

```
docker run -e NEO4J_AUTH=neo4j1/neo4j1 -p 7474:7474 -p 7687:7687 -v $(pwd)/import:/_import_csv --volume=$(pwd)/data:/data neo4j:3.4 /bin/bash

docker run -e NEO4J_AUTH=neo4j1/neo4j1 -p 7474:7474 -p 7687:7687 -v $(pwd)/import:/_import_csv neo4j:3.4 /bin/bash

./bin/neo4j-admin import --id-type STRING --nodes:Neuron /_import_csv/neurons.csv --relationships:SYN /_import_csv/synapses.csv && neo4j start

```
