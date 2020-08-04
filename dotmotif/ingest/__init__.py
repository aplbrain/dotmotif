# Standard installs:
import abc
import json
import os
import numbers

# Non-standard installs:
import dask.dataframe as dd
import pandas as pd

# Types only:
from typing import List
import networkx as nx

from .. import utils


class NetworkXConverter(abc.ABC):
    """
    An abstract base class for import to the NetworkX format.

    """

    pass

    def to_graph(self) -> nx.Graph:
        ...


class CSVEdgelistConverter(NetworkXConverter):
    """
    A converter that takes an arbitrary CSV file on disk and converts it to a graph.

    """

    def __init__(
        self, filepath: str, u_id_column: str, v_id_column: str, directed: bool = True
    ):
        data = pd.read_csv(filepath, dtype={u_id_column: str, v_id_column: str,})
        self._graph = nx.DiGraph() if directed else nx.Graph()
        for i, row in data.iterrows():
            self._graph.add_edge(
                str(row[u_id_column]), str(row[v_id_column]), **dict(row)
            )

    def to_graph(self):
        return self._graph


class Ingester:
    """
    Base ingester class
    """

    def ingest(self) -> List[str]:
        """
        Ingest the data and output a list of files where the data were saved.
        """
        ...


class FileIngester(Ingester):
    """
    Base class for ingester from a file on disk (or file-like).

    Abstract class, should not be used directly.
    """

    def __init__(self, path: str, export_dir: str) -> None:
        """
        Store the path and export directory of this ingester.

        All ingesters must have an input file(s) and an output directory which
        can be used by the dotmotif class for input to, say, a Neo4j docker
        container, among other platforms.
        """
        self.path = path
        self.export_dir = export_dir.rstrip("/") + "/"
        if not os.path.isdir(self.export_dir):
            os.makedirs(self.export_dir)


class NetworkXIngester:
    """
    An ingester that converts an in-memory networkx graph into two files:

    One file contains the node IDs and their attrs, and the other contains
    the edges and the edge attrs. Each column must contain a type annotation
    in order for Neo4j to be able to interpret the attributes as variables.
    """

    def __init__(self, graph: nx.Graph, export_dir: str) -> None:
        """
        Create a new ingester from networkx format.

        Arguments:
            graph (nx.Graph): The in-memory graph to ingest
            export_dir (str): The path to the CSV directory to use

        """
        self.export_dir = export_dir.rstrip("/") + "/"
        self.graph = graph

    def ingest(self) -> List[str]:
        def _pd_cypher_dtype_map(dtype):
            _valid_cypher_dtypes = [
                # https://neo4j.com/docs/operations-manual/current/tools/import/file-header-format/
                "int",
                "long",
                "float",
                "double",
                "boolean",
                "byte",
                "short",
                # "char", "string",
                # "point", "date", "localtime", "time", "localdatetime", "datetime", "duration"
            ]
            # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.api.types.infer_dtype.html
            return {
                "object": "string",
                "string": "string",
                "bytes": "string",
                "mixed-integer-float": "float",
                "floating": "float",
                "integer": "int",
                "mixed-integer": "int",
            }.get(pd.api.types.infer_dtype(dtype, skipna=True), "string")

        # First make sure that none of the IDs are numbers:
        for n in self.graph.nodes():
            if isinstance(n, (int, float)):
                raise ValueError(
                    "DotMotif does not support haystack graphs with numerical IDs. "
                    + "Not all executors can operate on numerical-ID graphs, and so "
                    + "they are disallowed. "
                    + "Learn more at https://github.com/aplbrain/dotmotif/issues/26"
                )

        # Now create a node-attribute dataframe:
        nodes_df = pd.DataFrame(
            {"neuronId:ID(Neuron)": u, **attrs}
            for u, attrs in self.graph.nodes(data=True)
        )

        # And edges:
        edges_df = pd.DataFrame(
            {":START_ID(Neuron)": u, ":END_ID(Neuron)": v, **attrs}
            for u, v, attrs in self.graph.edges(data=True)
        )

        edges_df.columns = [
            f"{c}"
            + (f":{_pd_cypher_dtype_map(edges_df[c])}" if "(Neuron)" not in c else "")
            for c in edges_df.columns
        ]

        nodes_df.columns = [
            f"{c}"
            + (f":{_pd_cypher_dtype_map(nodes_df[c])}" if "(Neuron)" not in c else "")
            for c in nodes_df.columns
        ]

        # Export the files:
        os.makedirs(f"{self.export_dir}", exist_ok=True)

        nodes_df.to_csv(f"{self.export_dir}/export-neurons-0.csv")
        edges_df.to_csv(f"{self.export_dir}/export-synapses-zdata.csv")

        return [
            f"{self.export_dir}/export-neurons-0.csv",
            f"{self.export_dir}/export-synapses-zdata.csv",
        ]


class _deprecated_Type2FileIngester(FileIngester):
    """
    An Ingester that reads data in the Type 2 CSV file format.

    The data are an edge-list, with extra columns that are currently
    ignored after ingest.
    """

    def __init__(self, path: str, export_dir: str) -> None:
        """
        Create a new ingester.

        .
        """
        super().__init__(path, export_dir)

    def ingest(self) -> List[str]:
        """
        Ingest using dask and pandas.

        .
        """
        df = dd.read_csv(self.path).dropna()
        export_df = df.copy()
        export_df[":START_ID(Neuron)"] = df["presyn_segid"].astype("int")
        export_df[":END_ID(Neuron)"] = df["postsyn_segid"].astype("int")
        for col in df.columns:
            del export_df[col]

        node_names = (
            (export_df[":START_ID(Neuron)"].append(export_df[":END_ID(Neuron)"]))
            .unique()
            .dropna()
        )

        node_fnames = node_names.to_csv(
            self.export_dir + "export-neurons-*.csv",
            index=False,
            header=["neuronId:ID(Neuron)"],
        )

        # This is absurd, but neo4j can't tolerate file headers in every CSV,
        # and dask can't NOT.
        # So We print off a header file first.
        headerpath = self.export_dir + "export-synapses-header.csv"
        with open(headerpath, "w") as headerfile:
            headerfile.write(":START_ID(Neuron),:END_ID(Neuron)")

        edge_fnames = export_df.to_csv(
            self.export_dir + "export-synapses-zdata-*.csv", index=False, header=False
        )

        return node_fnames + [headerpath] + edge_fnames


class _deprecated_Type1FileIngester(FileIngester):
    def __init__(self, path: str, export_dir: str) -> None:
        """
        Create a new ingester.
        """
        super().__init__(path, export_dir)

    def ingest(self) -> List[str]:
        """
        Ingest using dask and pandas.
        """
        data = json.load(open(self.path, "r"))
        export_df = pd.DataFrame(
            {":START_ID(Neuron)": data["neuron_1"], ":END_ID(Neuron)": data["neuron_2"]}
        )

        node_names = (
            export_df[":START_ID(Neuron)"].append(export_df[":END_ID(Neuron)"])
        ).unique()

        node_names_dd = dd.from_pandas(
            pd.DataFrame({"neuronId:ID(Neuron)": node_names}), npartitions=1
        )

        node_fnames = node_names_dd.to_csv(
            self.export_dir + "export-neurons-*.csv",
            index=False,
            header=["neuronId:ID(Neuron)"],
        )

        # This is absurd, but neo4j can't tolerate file headers in every CSV,
        # and dask can't NOT.
        # So We print off a header file first.
        export_df_dd = dd.from_pandas(export_df, npartitions=1)
        headerpath = self.export_dir + "export-synapses-header.csv"
        with open(headerpath, "w") as headerfile:
            headerfile.write(":START_ID(Neuron),:END_ID(Neuron)")

        edge_fnames = export_df_dd.to_csv(
            self.export_dir + "export-synapses-zdata-*.csv", index=False, header=False
        )

        return node_fnames + [headerpath] + edge_fnames
