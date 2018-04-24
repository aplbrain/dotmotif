<p align="center">
 <h1 align="center" fontsize="2em">d o t m o t i f</h1>
</p>
<p align="center">find brain-graph motifs in familiar notation</p>

# Usage

## Constructing a Query

### Writing a motif

You can currently write motifs in one of two languages; either CSV (in edge-list notation), or dotmotif form, which provides extra specificity when searching a graph (such as synapse polarity).

The following two files are equivalent:

```
fourcycle.csv
```
```
A,B
B,C,
C,A
```

```
fourcycle.motif
```
```
# A excites B
A -+ B
# B inhibits C
B -~ C
# We do not know how C influences A
C -? A
```

### Ingesting the motif into dotmotif

```python
from dotmotif import dotmotif

dm = dotmotif().from_csv("fourcycle.csv")

# or:
dm = dotmotif().from_motif("fourcycle.motif")
