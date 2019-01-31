#!/usr/bin/env python3

"""
Utilities for dotmotif.

Requires nx>=2.0
"""
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


def draw_motif(dm, negative_edge_color: str = "r", pos=None):
    """
    Draw a dotmotif motif object.

    Arguments:
        dm: dotmotif.DotMotif
        negative_edge_color (str: r): Color used to represent negative edges
        pos (dict: None): The position to use. If unset, uses nx.spring_layout

    Returns:
        None

    """
    if pos is None:
        pos = nx.spring_layout(dm._g)
    exc_edges = list(
        filter(lambda e: e[2].get("action", "") == "EXCITES", dm._g.edges(data=True))
    )
    inh_edges = list(
        filter(lambda e: e[2].get("action", "") == "INHIBITS", dm._g.edges(data=True))
    )
    nx.draw_networkx_edges(
        dm._g,
        pos=pos,
        edgelist=exc_edges,
        edge_color=[
            "k" if e["exists"] else negative_edge_color for u, v, e in exc_edges
        ],
    )
    nx.draw_networkx_edges(
        dm._g,
        pos=pos,
        edgelist=inh_edges,
        edge_color=[
            "k" if e["exists"] else negative_edge_color for u, v, e in inh_edges
        ],
        arrowstyle="-[",
    )
    nx.draw_networkx_nodes(dm._g, pos=pos, c="b")
    nx.draw_networkx_labels(dm._g, pos=pos)
