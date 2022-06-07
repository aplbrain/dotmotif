#!/usr/bin/env python3

"""
Utilities for dotmotif.

Requires nx>=2.0
"""
import hashlib
import json
import networkx as nx


def untype_string(string):
    try:
        return eval(string)
    except:
        try:
            if int(string) == float(string):
                return int(string)
            return float(string)
        except:
            return str(string)


def _hashed_dict(data: dict) -> str:
    """
    Return a unique hex color for a dictionary (six hex digits)

    Dicts with the same data (even in a different order) should return the same
    color hash.

    Arguments:
        data (dict): The data to hash

    Returns:
        str: A unique hex color for the data

    """
    if len(data) == 0:
        return "#00babe"
    encoded = json.dumps(data, sort_keys=True).encode()
    return "#" + hashlib.sha256(encoded).hexdigest()[:6]


def draw_motif(
    dm, negative_edge_color: str = "r", pos=None, labels: bool = True, **kwargs
):
    """
    Draw a dotmotif motif object.

    Arguments:
        dm: dotmotif.Motif
        negative_edge_color (str: r): Color used to represent negative edges
        pos (dict: None): The position to use. If unset, uses nx.spring_layout

    Returns:
        None

    """
    if pos is None:
        pos = nx.spring_layout(dm._g)
    exc_edges = list(
        filter(lambda e: e[2].get("action", "") == "SYN", dm._g.edges(data=True))
    )
    inh_edges = list(
        filter(lambda e: e[2].get("action", "") != "SYN", dm._g.edges(data=True))
    )

    positive_width = kwargs.get("edge_width", 3)
    negative_width = kwargs.get("negative_edge_width", kwargs.get("edge_width", 3))
    nx.draw_networkx_edges(
        dm._g,
        pos=pos,
        edgelist=exc_edges,
        width=[
            positive_width if e["exists"] else negative_width for u, v, e in exc_edges
        ],
        edge_color=[
            "k" if e["exists"] else negative_edge_color for u, v, e in exc_edges
        ],
        arrowsize=20,
        connectionstyle="arc3,rad=0.1",
    )
    nx.draw_networkx_edges(
        dm._g,
        pos=pos,
        edgelist=inh_edges,
        width=[
            positive_width if e["exists"] else negative_width for u, v, e in exc_edges
        ],
        edge_color=[
            "k" if e["exists"] else negative_edge_color for u, v, e in inh_edges
        ],
        arrowsize=20,
        arrowstyle="-[",
        connectionstyle="arc3,rad=0.1",
    )
    nx.draw_networkx_nodes(
        dm._g,
        pos=pos,
        node_color=[_hashed_dict(dm._node_constraints.get(n, {})) for n in dm._g.nodes],
    )
    if labels:
        nx.draw_networkx_labels(dm._g, pos=pos)


def _deep_merge_constraint_dicts(d1, d2):
    """
    Merge two dictionaries recursively.

    Arguments:
        d1 (dict): The first dictionary
        d2 (dict): The second dictionary

    Returns:
        dict: The merged dictionary

    """
    for k, v in d2.items():
        if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
            d1[k] = _deep_merge_constraint_dicts(d1[k], v)

        # Concat lists:
        elif k in d1 and isinstance(d1[k], list) and isinstance(v, list):
            d1[k] += v

        else:
            d1[k] = v
    return d1
