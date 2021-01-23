## *Class* `Motif`


Container class for dotmotif operations.

See __init__ documentation for more details.


## *Function* `__init__(self, input_motif: str = None, **kwargs)`


Create a new dotmotif object.

### Arguments
> - **input_motif** (`str`: `None`): Optionally, a DotMotif DSL defined motif,
        or a path to a .motif file that contains a motif.
> - **ignore_direction** (`bool`: `False`): Whether to disregard direction when
        generating the database query
> - **limit** (`int`: `None`): A limit (if any) to impose on the query results
> - **enforce_inequality** (`bool`: `False`): Whether to enforce inequality; in
        other words, whether two nodes should be permitted to be aliases         for the same node. For example, A>B>C; if A!=C, then set to True
> - **bool** (`None`: `None`): True)
> - **parser** (`dotmotif.parsers.Parser`: `DEFAULT_MOTIF_PARSER`): The parser
        to use to parse the document. Defaults to the v2 parser.
> - **exclude_automorphisms** (`bool`: `False`): Whether to exclude automorphism
        variants of the motif when rturning results.
> - **validators** (`List[Validator]`: `None`): A list of dotmotif.Validators to use
        when verifying the motif for correctness and executability.



## *Function* `from_motif(self, cmd: str)`


Ingest a dotmotif-format string.

### Arguments
> - **cmd** (`str`: `None`): A string in dotmotif form, or a .dm filename on disk

### Returns
    A pointer to this dotmotif object, for chaining



## *Function* `from_nx(self, graph: nx.DiGraph) -> "dotmotif"`


Ingest directly from a graph.

### Arguments
> - **graph** (`nx.DiGraph`: `None`): The graph to import

### Returns
    None



## *Function* `to_nx(self) -> nx.DiGraph`


Output a networkx graph describing the motif.

### Returns
    networkx.DiGraph



## *Function* `save(self, fname: Union[str, IO[bytes]]) -> Union[str, IO[bytes]]`


Save the motif to a file on disk.

### Arguments
> - **fname** (`str`: `None`): A path on disk for IO

### Returns
    Pointer to File-like.



## *Function* `load(fname: Union[str, IO[bytes]]) -> "dotmotif"`


Load the motif from a file on disk.

### Arguments
> - **fname** (`str`: `None`): A path on disk for IO

### Returns
    Pointer to File-like.

