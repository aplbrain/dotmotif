## *Class* `Neo4jExecutor(Executor)`


A Neo4j executor that runs Cypher queries against a running Neo4j database.

.


## *Function* `__init__(self, **kwargs) -> None`


Create a new executor.

If there is an already-running Neo4j database, you can pass in authentication information and it will connect.

If there is no existing database, you can pass in a graph to ingest and the executor will connect to it automatically.

If there is no existing database and you do not pass in a graph, you must pass an `import_directory`, which the container will mount as an importable CSV resource.

### Arguments
> - **db_bolt_uri** (`str`: `None`): If connecting to an existing server, the URI
        of the server (including the port, probably 7474).
> - **username** (`str`: `"neo4j"`): The username to use to attach to an
        existing server.
> - **password** (`str`: `None`): The password to use to attach to an existing server.
> - **graph** (`nx.Graph`: `None`): If provisioning a new database, the networkx
        graph to import into the database.
> - **import_directory** (`str`: `None`): If provisioning a new database, the local
        directory to crawl for CSVs to import into the Neo4j database.         Commonly used when you want to quickly and easily start a new         Executor that uses the export from a previous graph.
> - **autoremove_container** (`bool`: `True`): Whether to delete the container
        when the executor is deconstructed. Set to False if you'd like         to be able to connect with other executors after the first one         has closed.
> - **max_memory** (`str`: `"4G"`): The maximum amount of memory to provision.
> - **initial_memory** (`str`: `"2G"`): The starting heap-size for the Neo4j
        container's JVM.
> - **max_retries** (`int`: `20`): The number of times DotMotif should try to
        connect to the neo4j container before giving up.
> - **wait_for_boot** (`bool`: `True`): Whether the process should pause to
        wait for a provisioned Docker container to come online.
> - **entity_labels** (`dict`: `_DEFAULT_ENTITY_LABELS`): The set of labels to
        use for nodes and edges.



## *Function* `__del__(self)`


Destroy the docker container from the running processes.

Also will handle (TODO) other teardown actions.


## *Function* `create_index(self, attribute_name: str)`


Create a new index on the given node attribute.

Note that edge attributes are NOT supported.


## *Function* `run(self, cypher: str, cursor=True)`


Run an arbitrary cypher command.

You should usually ignore this, and use .find() instead.

### Arguments
> - **cypher** (`str`: `None`): The command to run

### Returns
    The result of the cypher query (py2neo.Table)



## *Function* `count(self, motif: "dotmotif", limit=None) -> int`


Count a motif in a larger graph.

### Arguments
    motif (dotmotif.dotmotif)



## *Function* `find(self, motif: "dotmotif", limit=None, cursor=True)`


Find a motif in a larger graph.

### Arguments
    motif (dotmotif.dotmotif)

