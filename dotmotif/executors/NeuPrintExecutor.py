import pandas as pd
from neuprint import Client

from .Neo4jExecutor import Neo4jExecutor

_LOOKUP = {
    "INHIBITS": "ConnectsTo",
    "EXCITES": "ConnectsTo",
    "SYNAPSES": "ConnectsTo",
    "INH": "ConnectsTo",
    "EXC": "ConnectsTo",
    "SYN": "ConnectsTo",
}


class NeuPrintExecutor(Neo4jExecutor):
    def __init__(self, host: str, dataset: str, token: str) -> None:
        self._created_container = False
        self.host = host
        self.dataset = dataset
        self.token = token
        self.client = Client(host, dataset=self.dataset, token=self.token)

    def run(self, cypher: str) -> pd.DataFrame:
        """
        Run an arbitrary cypher command.

        You should usually ignore this, and use .find() instead.

        Arguments:
            cypher (str): The command to run

        Returns:
            The result of the cypher query

        """
        return self.client.fetch_custom(cypher)

    def count(self, motif: "dotmotif", limit=None) -> int:
        """
        Count a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif)

        """
        qry = self.motif_to_cypher(motif, count_only=True, edge_name_lookup=_LOOKUP)
        if limit:
            qry += f" LIMIT {limit}"
        res = self.client.fetch_custom(qry)
        print(res)
        return int(res.to_numpy())

    def find(self, motif: "dotmotif", limit=None) -> pd.DataFrame:
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif)

        """
        qry = self.motif_to_cypher(motif, edge_name_lookup=_LOOKUP)
        if limit:
            qry += f" LIMIT {limit}"
        return self.client.fetch_custom(qry)

    @staticmethod
    def motif_to_cypher(
        motif: "dotmotif", count_only: bool = False, edge_name_lookup: dict = None
    ) -> str:
        edge_name_lookup = edge_name_lookup or _LOOKUP
        return Neo4jExecutor.motif_to_cypher(motif, count_only, edge_name_lookup)

