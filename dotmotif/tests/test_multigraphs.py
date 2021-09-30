import networkx as nx
import pytest

from dotmotif.executors.NetworkXExecutor import NetworkXExecutor
from dotmotif.executors.GrandIsoExecutor import GrandIsoExecutor
from dotmotif import Motif

@pytest.mark.parametrize("executor", [NetworkXExecutor, GrandIsoExecutor])
def test_multidigraph_all_edges(executor):
    """
    Test that multigraph support works in GrandIso and NetworkX executors.

    Test setting `multigraph_match_all_edges = True`.
    """

    haystack = nx.MultiDiGraph()
    haystack.add_edge("A", "B", size=10)
    haystack.add_edge("A", "B", size=20)

    motif = Motif("""
    a -> b [size > 9]
    """)

    results = executor(graph=haystack, multigraph_match_all_edges=True).find(motif)

    assert len(results) == 1


@pytest.mark.parametrize("executor", [NetworkXExecutor, GrandIsoExecutor])
def test_multigraph_any_edges(executor):
    """
    Test that multigraph support works in GrandIso and NetworkX executors.

    Test setting `multigraph_match_all_edges = False`.
    """

    haystack = nx.MultiDiGraph()
    haystack.add_edge("A", "B", size=10)
    haystack.add_edge("A", "B", size=20)

    motif = Motif("""
    a -> b [size > 15]
    """)

    results = executor(graph=haystack, multigraph_match_all_edges=False).find(motif)

    assert len(results) == 1

@pytest.mark.parametrize("executor", [NetworkXExecutor, GrandIsoExecutor])
def test_cannot_specify_both_all_and_any(executor):
    """
    Test that multigraph support works in GrandIso and NetworkX executors.

    Test setting both `multigraph_match_all_edges` and `multigraph_match_any_edge` to True.
    """

    haystack = nx.MultiDiGraph()
    with pytest.raises(ValueError):
        executor(graph=haystack, multigraph_match_all_edges=True, multigraph_match_any_edge=True)

@pytest.mark.parametrize("executor", [NetworkXExecutor, GrandIsoExecutor])
def test_impossible_constraint_works_on_multigraph(executor):
    """
    Tests that an "impossible" constraint on a simple graph works on a multigraph.
    """

    haystack = nx.MultiDiGraph()
    haystack.add_edge("A", "B", size=10)
    haystack.add_edge("A", "B", size=20)
    haystack.add_edge("B", "C", size=30)
    haystack.add_edge("B", "C", size=40)

    motif = Motif("""
    a -> b [size >= 15, size < 19]
    """)

    results = executor(graph=haystack, multigraph_match_any_edge=True).find(motif)

    assert len(results) == 1

    results = executor(graph=haystack, multigraph_match_all_edges=True).find(motif)

    assert len(results) == 0

    results = executor(graph=nx.DiGraph(haystack)).find(motif)

    assert len(results) == 0

