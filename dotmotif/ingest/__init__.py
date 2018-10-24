# Standard installs:
import json
import os

# Non-standard installs:
import dask.dataframe as dd
import pandas as pd

# Types only:
from typing import List

class Ingester:
    ...


class PrincetonIngester(Ingester):
    def __init__(self, csvpath: str, export_dir: str) -> None:
        self.csvpath = csvpath
        self.export_dir = export_dir.rstrip("/") + "/"
        if not os.path.isdir(self.export_dir):
            os.makedirs(self.export_dir)

    def ingest(self) -> List[str]:
        df = dd.read_csv(self.csvpath).dropna()
        export_df = df.copy()
        export_df[":START_ID(Neuron)"] = df["cleft_segid"].astype('int')
        export_df[":END_ID(Neuron)"] = df["postsyn_segid"].astype('int')
        for col in df.columns:
            del export_df[col]

        node_names = (
            export_df[":START_ID(Neuron)"].append(export_df[":END_ID(Neuron)"])
        ).unique().dropna()

        node_fnames = node_names.to_csv(
            self.export_dir + "export-neurons-*.csv",
            index=False, header=["neuronId:ID(Neuron)"]
        )

        # This is absurd, but neo4j can't tolerate file headers in every CSV,
        # and dask can't NOT.
        # So We print off a header file first.
        headerpath = self.export_dir + "export-synapses-00.csv"
        with open(headerpath, 'w') as headerfile:
            headerfile.write(":START_ID(Neuron),:END_ID(Neuron)")

        edge_fnames = export_df.to_csv(
            self.export_dir + "export-synapses-*.csv", index=False, header=False
        )

        return node_fnames + [headerpath] + edge_fnames


class HarvardIngester(Ingester):

    def __init__(self, json_path: str, export_dir: str) -> None:
        self.json_path = json_path
        self.export_dir = export_dir.rstrip("/") + "/"
        if not os.path.isdir(self.export_dir):
            os.makedirs(self.export_dir)

    def ingest(self) -> List[str]:
        data = json.load(open(self.json_path, 'r'))
        export_df = pd.DataFrame({
            ":START_ID(Neuron)": data["neuron_1"],
            ":END_ID(Neuron)":   data["neuron_2"]
        })

        node_names = (
            export_df[":START_ID(Neuron)"].append(export_df[":END_ID(Neuron)"])
        ).unique()

        node_names_dd = dd.from_pandas(pd.DataFrame({
            "neuronId:ID(Neuron)": node_names
        }), npartitions=1)

        node_fnames = node_names_dd.to_csv(
            self.export_dir + "export-neurons-*.csv",
            index=False, header=["neuronId:ID(Neuron)"]
        )

        # This is absurd, but neo4j can't tolerate file headers in every CSV,
        # and dask can't NOT.
        # So We print off a header file first.
        export_df_dd = dd.from_pandas(export_df, npartitions=1)
        headerpath = self.export_dir + "export-synapses-00.csv"
        with open(headerpath, 'w') as headerfile:
            headerfile.write(":START_ID(Neuron),:END_ID(Neuron)")

        edge_fnames = export_df_dd.to_csv(
            self.export_dir + "export-synapses-*.csv", index=False, header=False
        )

        return node_fnames + [headerpath] + edge_fnames
