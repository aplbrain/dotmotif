## *Class* `NeuPrintExecutor(Neo4jExecutor)`


A NeuPrintExecutor may be used to access an existing neuPrint server.

This class converts a DotMotif motif object into a neuPrint-compatible query. Not all neuPrint datatypes or query types are available, but this adds complete support for DotMotif motif searches by passing raw Cypher queries to the neuPrint server over the HTTP API.

Note that the neuPrint default timeout is quite short, and slower motif queries may not run in time.



## *Function* `__init__(self, host: str, dataset: str, token: str) -> None`


Create a new NeuPrintExecutor that points to a deployed neuPrint DB.

### Arguments
> - **host** (`str`: `None`): The host of the neuPrint server (for example,
        'neuprint.janelia.org')
> - **dataset** (`str`: `None`): The name of the dataset to reference (for example,
        'hemibrain:v1.1`)
> - **token** (`str`: `None`): The user's neuPrint access token. To retrieve this
        token, go to https://[host]/account.

### Returns
    None



## *Function* `run(self, cypher: str) -> pd.DataFrame`


Run an arbitrary cypher command.

You should usually ignore this, and use .find() instead.

### Arguments
> - **cypher** (`str`: `None`): The command to run

### Returns
    The result of the cypher query



## *Function* `count(self, motif: "dotmotif", limit=None) -> int`


Count a motif in a larger graph.

### Arguments
> - **motif** (`dotmotif.dotmotif`: `None`): The motif to search for

### Returns
> - **int** (`None`: `None`): The count of this motif in the host graph



## *Function* `find(self, motif: "dotmotif", limit=None) -> pd.DataFrame`


Find a motif in a larger graph.

### Arguments
> - **motif** (`dotmotif.dotmotif`: `None`): The motif to search for

### Returns
> - **pd.DataFrame** (`None`: `None`): The results of the search

