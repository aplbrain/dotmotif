
"""

## Multigraph Support

The host graph argument to `NetworkXExecutor` and `GrandIsoExecutor` can be a
`nx.MultiDiGraph` or `nx.MultiGraph`. If the host graph is a `nx.MultiDiGraph`,
then the user can specify whether they would like to match all edges or any edge.

If the user wants ALL edges between two nodes to satisfy the constraints (e.g.,
`a -> b [size > 10]`) for all edges between nodes `a` and `b`) then they should
set `multigraph_match_all_edges = True`.

If the user wants the mapping to succeed if ANY edge between two nodes satisfies
the constraints (e.g., `a -> b [size > 10]` is true for at least one of the
edges between `a` and `b`) then they should set `multigraph_match_any_edge = True`.


"""

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
def test_multigraph_basic(executor):
    """
    Test that we can match the "basic" case where one attribute is specified
    per edge, and one edge between two nodes satisfies it.
    """

    haystack = nx.MultiDiGraph()
    haystack.add_edge("A", "B", size=10)
    haystack.add_edge("A", "B", size=20)
    haystack.add_edge("B", "C", size=20)

    motif = Motif("""
    a -> b [size > 15]
    """)

    results = executor(graph=haystack, multigraph_match_any_edge=True).find(motif)
    assert len(results) == 2
    results = executor(graph=haystack, multigraph_match_all_edges=True).find(motif)
    assert len(results) == 1

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

