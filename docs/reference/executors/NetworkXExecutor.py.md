## *Function* `_edge_satisfies_constraints(edge_attributes: dict, constraints: dict) -> bool`


Check if a single edge satisfies the constraints.


## *Function* `_node_satisfies_constraints(node_attributes: dict, constraints: dict) -> bool`


Check if a single node satisfies the constraints.



## *Class* `NetworkXExecutor(Executor)`


A query executor that runs inside RAM.

Uses NetworkX's built-in (VF2) subgraph isomorphism algo. Good for very small graphs, since this won't scale particularly well.


## *Function* `__init__(self, **kwargs) -> None`


Create a new NetworkXExecutor.

### Arguments
    graph (networkx.Graph)

### Returns
    None



## *Function* `count(self, motif: "dotmotif", limit: int = None)`


Count the occurrences of a motif in a graph.

See NetworkXExecutor#find for more documentation.


## *Function* `find(self, motif: "dotmotif", limit: int = None)`


Find a motif in a larger graph.

### Arguments
    motif (dotmotif.dotmotif)

