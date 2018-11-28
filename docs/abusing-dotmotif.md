# Doing something nasty to DotMotif so that you can just use it for its database

DotMotif does a lot of heavy-lifting so that you can ignore the fact that you're using a graph database. This can come in handy when you want to use a graph database but don't want to do work to set it up. 

DotMotif does the following for you:

* Attaches to a graph database if available
* Provisions a docker container if no graph database is available
* Imports your data from a variety of formats
* Authenticates with the database
* Sets a new password (mandatory for new neo4j databases)
* Provides an avenue for you to query the database

## Using DotMotif to create a database

We don't need most of the dotmotif capabilities if we're not trying to run a subgraph isomorphism query, so we can ignore the `dotmotif` class altogether. Instead, run the following:

```python
>>> # Imagine you have a graph of type networkx.DiGraph called G:
>>> G = nx.DiGraph(...)
```
```python
>>> from dotmotif.executors import Neo4jExecutor
>>> E = Neo4jExecutor(graph=G)
```
You will need to wait a few minutes now (may be even longer depending on if you have already pulled down the neo4j docker image previously, and, thither, your internet speed).

Once that completes, you will have access to the neo4j shell to execute commands. You can either use this for good (i.e. dotmotif queries) or evil (i.e. anything else you want to run on a graph database). Note that if you are exposing this graph database to the world, this procedure is INSECURE and gives others admin access to the database.
```python
>>> E.run(cypher_query)
```

...where `cypher_query` is a query....that you wrote...in cypher.

## Take it from the top

An example, given a simple graph:

```python
import networkx as nx
G = nx.DiGraph()
G.add_path([1, 2, 3])

from dotmotif.executors import Neo4jExecutor
E = Neo4jExecutor(graph=G)

E.run("SELECT (A)-[B]->(C) RETURN DISTINCT A, B, C")
# returns [[1, 2], [2, 3]]
```
