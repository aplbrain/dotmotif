import pandas as pd
from neuprint import Client

from .. import dotmotif
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
    """
    A NeuPrintExecutor may be used to access an existing neuPrint server.

    This class converts a DotMotif motif object into a neuPrint-compatible
    query. Not all neuPrint datatypes or query types are available, but this
    adds complete support for DotMotif motif searches by passing raw Cypher
    queries to the neuPrint server over the HTTP API.

    Note that the neuPrint default timeout is quite short, and slower motif
    queries may not run in time.

    """

    def __init__(self, host: str, dataset: str, token: str) -> None:
        """
        Create a new NeuPrintExecutor that points to a deployed neuPrint DB.

        Arguments:
            host (str): The host of the neuPrint server (for example,
                'neuprint.janelia.org')
            dataset (str): The name of the dataset to reference (for example,
                'hemibrain:v1.1`)
            token (str): The user's neuPrint access token. To retrieve this
                token, go to https://[host]/account.

        Returns:
            None

        """
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

    def count(self, motif: dotmotif, limit=None) -> int:
        """
        Count a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif): The motif to search for

        Returns:
            int: The count of this motif in the host graph

        """
        qry = self.motif_to_cypher(motif, count_only=True, edge_name_lookup=_LOOKUP)
        if limit:
            qry += f" LIMIT {limit}"
        res = self.client.fetch_custom(qry)
        print(res)
        return int(res.to_numpy())

    def find(self, motif: dotmotif, limit=None) -> pd.DataFrame:
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.dotmotif): The motif to search for

        Returns:
            pd.DataFrame: The results of the search

        """
        qry = self.motif_to_cypher(motif, edge_name_lookup=_LOOKUP)
        if limit:
            qry += f" LIMIT {limit}"
        return self.client.fetch_custom(qry)

    @staticmethod
    def motif_to_cypher(
        motif: dotmotif, count_only: bool = False, edge_name_lookup: dict = None
    ) -> str:
        """
        Convert a motif to neuprint-flavored Cypher.

        This is currently a thin passthrough for Neo4jExecutor.motif_to_cypher.

        """
        edge_name_lookup = edge_name_lookup or _LOOKUP
        return Neo4jExecutor.motif_to_cypher(motif, count_only, edge_name_lookup)

