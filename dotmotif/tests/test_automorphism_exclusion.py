import itertools

import networkx as nx
import pytest

import dotmotif
from dotmotif.executors import GrandIsoExecutor, NetworkXExecutor


def _host():
    G = nx.gnp_random_graph(20, 0.18, seed=3, directed=True)
    for n in G.nodes:
        G.nodes[n]["t"] = "x" if n % 2 else "y"
        G.nodes[n]["r"] = n % 5
    return G


def _distinct_matches(G, present, absent, node_t, dyn_gt=()):
    """Brute-force count of distinct subgraphs: labeled matches / |Aut|."""
    names = sorted({c for e in present + absent for c in e} | set(node_t))

    def ok(m):
        return (
            all(G.has_edge(m[a], m[b]) for a, b in present)
            and not any(G.has_edge(m[a], m[b]) for a, b in absent)
            and all(G.nodes[m[k]]["t"] == v for k, v in node_t.items())
            and all(G.nodes[m[a]]["r"] > G.nodes[m[b]]["r"] for a, b in dyn_gt)
        )

    labeled = sum(
        ok(dict(zip(names, tup))) for tup in itertools.permutations(G.nodes, len(names))
    )
    aut = 0
    for p in itertools.permutations(names):
        s = dict(zip(names, p))
        if (
            {(s[a], s[b]) for a, b in present} == set(present)
            and {(s[a], s[b]) for a, b in absent} == set(absent)
            and all(node_t.get(s[k]) == node_t.get(k) for k in names)
            and {(s[a], s[b]) for a, b in dyn_gt} == set(dyn_gt)
        ):
            aut += 1
    assert labeled % aut == 0
    return labeled // aut


CASES = {
    "induced chain": (
        [("A", "B"), ("B", "C")],
        [("B", "A"), ("C", "B"), ("A", "C"), ("C", "A")],
        {},
        (),
    ),
    "3-cycle": ([("A", "B"), ("B", "C"), ("C", "A")], [], {}, ()),
    "4-cycle": ([("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")], [], {}, ()),
    "typed diamond": (
        [("V", "S"), ("V", "P"), ("S", "E"), ("P", "E")],
        [],
        {"S": "x", "P": "y"},
        (),
    ),
    "untyped diamond": ([("V", "S"), ("V", "P"), ("S", "E"), ("P", "E")], [], {}, ()),
    "fan-out": ([("A", "B"), ("A", "C")], [], {}, ()),
    "fan-out with dynamic constraint": (
        [("A", "B"), ("A", "C")],
        [],
        {},
        (("B", "C"),),
    ),
    "reciprocal pair with shared input": (
        [("A", "B"), ("B", "A"), ("C", "A"), ("C", "B")],
        [],
        {},
        (),
    ),
}


def _motif_text(present, absent, node_t, dyn_gt):
    return "\n".join(
        [f"{a} -> {b}" for a, b in present]
        + [f"{a} !> {b}" for a, b in absent]
        + [f'{k}.t = "{v}"' for k, v in node_t.items()]
        + [f"{a}.r > {b}.r" for a, b in dyn_gt]
    )


@pytest.mark.parametrize("name", list(CASES))
@pytest.mark.parametrize("executor", [GrandIsoExecutor, NetworkXExecutor])
def test_exclude_automorphisms_matches_brute_force(name, executor):
    G = _host()
    present, absent, node_t, dyn_gt = CASES[name]
    motif = dotmotif.Motif(
        _motif_text(present, absent, node_t, dyn_gt), exclude_automorphisms=True
    )
    expected = _distinct_matches(G, present, absent, node_t, dyn_gt)
    assert len(executor(graph=G).find(motif)) == expected


def test_negative_edges_do_not_create_symmetry():
    motif = dotmotif.Motif(
        "A -> B\nB -> C\nB !> A\nC !> B\nA !> C\nC !> A", exclude_automorphisms=True
    )
    assert motif.list_automorphisms() == []


def test_node_constraints_break_symmetry():
    motif = dotmotif.Motif(
        'A -> B\nA -> C\nB.t = "x"\nC.t = "y"', exclude_automorphisms=True
    )
    assert motif.list_automorphisms() == []


def test_edge_constraints_break_symmetry():
    motif = dotmotif.Motif("A -> B [weight > 3]\nA -> C", exclude_automorphisms=True)
    assert motif.list_automorphisms() == []


def test_cycle_uses_one_base_node():
    motif = dotmotif.Motif("A -> B\nB -> C\nC -> A", exclude_automorphisms=True)
    assert sorted(motif.list_automorphisms()) == [("A", "B"), ("A", "C")]
