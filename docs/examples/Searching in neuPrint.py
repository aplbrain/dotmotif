import dotmotif
from dotmotif.executors.NeuPrintExecutor import NeuPrintExecutor

HOSTNAME = "neuprint.janelia.org"
DATASET = "hemibrain:v1.2.1"
TOKEN = "[YOUR TOKEN HERE]"

motif = dotmotif.Motif(
    """
    A -> B
    A['AVLP(R)'] = True
    """
)

E = NeuPrintExecutor(HOSTNAME, DATASET, TOKEN)

E.find(motif, limit=2)
