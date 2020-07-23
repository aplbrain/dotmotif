## *Class* `NetworkXConverter(abc.ABC)`


An abstract base class for import to the NetworkX format.



## *Class* `CSVEdgelistConverter(NetworkXConverter)`


A converter that takes an arbitrary CSV file on disk and converts it to a graph.



## *Class* `Ingester`


Base ingester class


## *Function* `ingest(self) -> List[str]`


Ingest the data and output a list of files where the data were saved.


## *Class* `FileIngester(Ingester)`


Base class for ingester from a file on disk (or file-like).

Abstract class, should not be used directly.


## *Function* `__init__(self, path: str, export_dir: str) -> None`


Store the path and export directory of this ingester.

All ingesters must have an input file(s) and an output directory which can be used by the dotmotif class for input to, say, a Neo4j docker container, among other platforms.


## *Class* `NetworkXIngester(Ingester)`


An ingester from the NetworkX in-memory format.

.


## *Function* `__init__(self, graph: nx.Graph, export_dir: str) -> None`


Create a new ingester from networkx format.

### Arguments
> - **graph** (`nx.Graph`: `None`): The in-memory graph to ingest
> - **export_dir** (`str`: `None`): The path to the CSV directory to use



## *Function* `ingest(self) -> List[str]`


Perform the ingest into a list of CSV filenames.

.


## *Class* `_deprecated_Type2FileIngester(FileIngester)`


An Ingester that reads data in the Type 2 CSV file format.

The data are an edge-list, with extra columns that are currently ignored after ingest.


## *Function* `__init__(self, path: str, export_dir: str) -> None`


Create a new ingester.

.


## *Function* `ingest(self) -> List[str]`


Ingest using dask and pandas.

.


## *Function* `__init__(self, path: str, export_dir: str) -> None`


Create a new ingester.


## *Function* `ingest(self) -> List[str]`


Ingest using dask and pandas.
