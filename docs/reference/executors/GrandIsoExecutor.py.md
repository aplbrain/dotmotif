## *Class* `GrandIsoExecutor(NetworkXExecutor)`


A DotMotif executor that uses grandiso for subgraph monomorphism.

This executor is dramatically fast than the NetworkX search, and is still a pure-Python implementation.

[GrandIso](https://github.com/aplbrain/grandiso-networkx)



## *Function* `find(self, motif, limit: int = None)`


Find a motif in a larger graph.

### Arguments
    motif (dotmotif.Motif)
> - **int** (`None`: `None`): None)

### Returns
    List[dict]

