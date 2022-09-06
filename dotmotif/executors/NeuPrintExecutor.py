import pandas as pd
from neuprint import Client

from .. import Motif
from .Neo4jExecutor import Neo4jExecutor

_LOOKUP = {
    "INHIBITS": "ConnectsTo",
    "EXCITES": "ConnectsTo",
    "SYNAPSES": "ConnectsTo",
    "INH": "ConnectsTo",
    "EXC": "ConnectsTo",
    "SYN": "ConnectsTo",
    "DEFAULT": "ConnectsTo",
}

_DEFAULT_ENTITY_LABELS = {
    "node": "Neuron",
    "edge": _LOOKUP,
}

_ROI_INFO_JSON_ATTRIBUTES = [
    "SNP(R)",
    "SMP(R)",
    "SNP(L)",
    "SMP(L)",
    "SIP(L)",
    "SIP(R)",
    "INP",
    "CRE(L)",
    "CRE(-RUB)(L)",
    "CRE(R)",
    "CRE(-ROB,-RUB)(R)",
    "MB(R)",
    "b'L(R)",
    "b'2(R)",
    "MB(+ACA)(R)",
    "LX(R)",
    "LAL(R)",
    "LAL(-GA)(R)",
    "ROB(R)",
    "LX(L)",
    "LAL(L)",
    "VLNP(R)",
    "PVLP(R)",
    "PLP(R)",
    "VMNP",
    "VES(R)",
    "EPA(R)",
    "CX"
]


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

    def count(self, motif: Motif, limit=None) -> int:
        """
        Count a motif in a larger graph.

        Arguments:
            motif (dotmotif.Motif): The motif to search for

        Returns:
            int: The count of this motif in the host graph

        """
        qry = self.motif_to_cypher(
            motif, count_only=True, static_entity_labels=_DEFAULT_ENTITY_LABELS
        )
        if limit:
            qry += f" LIMIT {limit}"
        res = self.client.fetch_custom(qry)
        print(res)
        return int(res.to_numpy())

    def find(self, motif: Motif, limit=None) -> pd.DataFrame:
        """
        Find a motif in a larger graph.

        Arguments:
            motif (dotmotif.Motif): The motif to search for

        Returns:
            pd.DataFrame: The results of the search

        """
        qry = self.motif_to_cypher(motif, static_entity_labels=_DEFAULT_ENTITY_LABELS)
        if limit:
            qry += f" LIMIT {limit}"
        return self.client.fetch_custom(qry)

    @staticmethod
    def motif_to_cypher(
            motif: Motif, count_only: bool = False, static_entity_labels: dict = None
    ) -> str:
        """
        Convert a motif to neuprint-flavored Cypher.

        This is currently a thin passthrough for Neo4jExecutor.motif_to_cypher.

        """
        static_entity_labels = static_entity_labels or _DEFAULT_ENTITY_LABELS
        cypher = Neo4jExecutor.motif_to_cypher(motif, count_only, static_entity_labels)

        for (u, v), a in motif.list_edge_constraints().items():
            for key, constraints in a.items():
                key = key.strip('\"')  # remove quotes if any
                if key in _ROI_INFO_JSON_ATTRIBUTES:
                    for operator, values in constraints.items():
                        for value in values:
                            this_edge = """{}_{}["{}"] {} {}""".format(u, v, key, operator, str(value))
                            that_edge_pre = """(apoc.convert.fromJsonMap({}.roiInfo)["{}"].pre {} {})""".format(u, key,
                                                                                                                operator,
                                                                                                                str(value))
                            that_edge_post = """(apoc.convert.fromJsonMap({}.roiInfo)["{}"].post {} {})""".format(v,
                                                                                                                  key,
                                                                                                                  operator,
                                                                                                                  str(value))
                            cypher = cypher.replace(this_edge, that_edge_pre + " AND " + that_edge_post)
                else:
                    print("Unknown JSON edge constraint: {}".format(key))
        return cypher
