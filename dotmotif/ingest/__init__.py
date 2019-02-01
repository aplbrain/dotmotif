# Standard installs:
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


class NetworkXIngester(Ingester):
    def __init__(self, graph: nx.Graph, export_dir: str) -> None:
        self.export_dir = export_dir.rstrip("/") + "/"
        self.graph = graph

    def ingest(self) -> List[str]:
        # Export the graph to CSV (nodes and edges):

        all_node_attrs = {}
        for _, a in self.graph.nodes(data=True):
            for key, val in a.items():
                val = utils.untype_string(val)
                if key in all_node_attrs:
                    if isinstance(val, all_node_attrs[key]):
                        pass
                    else:
                        all_node_attrs[key] = str
                else:
                    if isinstance(val, (float, int)):
                        all_node_attrs[key] = float
                    else:
                        all_node_attrs[key] = str

        for k, v in all_node_attrs.items():
            all_node_attrs[k] = {str: "string", float: "float", int: "int"}[v]

        sorted_node_attrs = sorted(list(all_node_attrs.keys()))

        nodes_csv = (
            "neuronId:ID(Neuron),"
            + +",".join(
                ["{}:{}".format(k, all_node_attrs[k]) for k in sorted_node_attrs]
            )
            + "\n"
            + "\n".join(
                [
                    i + "," + ",".join([str(n.get(k, "") for k in sorted_node_attrs)])
                    for i, n in self.graph.nodes(True)
                ]
            )
        )

        # This huge mess is type inference to make the exported file convey the
        # types of the attributes, if available. String is the default.
        # TODO: Can probably be cleaned up!
        all_edge_attrs = {}
        for _, _, a in self.graph.edges(data=True):
            for key, val in a.items():
                val = utils.untype_string(val)
                if key in all_edge_attrs:
                    if isinstance(val, all_edge_attrs[key]):
                        pass
                    else:
                        all_edge_attrs[key] = str
                else:
                    if isinstance(val, (float, int)):
                        all_edge_attrs[key] = float
                    else:
                        all_edge_attrs[key] = str

        for k, v in all_edge_attrs.items():
            all_edge_attrs[k] = {str: "string", float: "float", int: "int"}[v]

        sorted_edge_attrs = sorted(list(all_edge_attrs.keys()))
        edges_csv = (
            ":START_ID(Neuron),:END_ID(Neuron),"
            + ",".join(
                ["{}:{}".format(k, all_edge_attrs[k]) for k in sorted_edge_attrs]
            )
            + "\n"
            + "\n".join(
                [
                    f"{u},{v},"
                    + ",".join([str(a.get(k, "")) for k in sorted_edge_attrs])
                    for u, v, a in self.graph.edges(data=True)
                ]
            )
        )

        # Export the files:
        try:
            os.makedirs(f"{self.export_dir}")
        except:
            pass

        with open(f"{self.export_dir}/export-neurons-0.csv", "w") as fh:
            fh.write(nodes_csv)
        with open(f"{self.export_dir}/export-synapses-zdata.csv", "w") as fh:
            fh.write(edges_csv)

        return [
            f"{self.export_dir}/export-neurons-0.csv",
            f"{self.export_dir}/export-synapses-zdata.csv",
        ]


class PrincetonIngester(FileIngester):
    """
    An Ingester that reads data in the Princeton CSV file format.

    The Princeton data are an edge-list, with extra columns that are currently
    ignored after ingest.
    """

    def __init__(self, path: str, export_dir: str) -> None:
        """
        Create a new ingester.
        """
        super().__init__(path, export_dir)

    def ingest(self) -> List[str]:
        """
        Ingest using dask and pandas.
        """
        df = dd.read_csv(self.path).dropna()
        export_df = df.copy()
        export_df[":START_ID(Neuron)"] = df["cleft_segid"].astype("int")
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


class HarvardIngester(FileIngester):
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
