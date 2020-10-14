from dotmotif import Motif, GrandIsoExecutor
from dotmotif.ingest import CSVEdgelistConverter


graph = CSVEdgelistConverter(
    "https://zenodo.org/record/3710459/files/soma_subgraph_synapses_spines_v185.csv?download=1",
    "pre_root_id",
    "post_root_id",
).to_graph()

E = GrandIsoExecutor(graph=graph)

motif = Motif(
    """
A -> B
B -> C
C -> A
"""
)

results = E.find(motif)

print(len(results))
