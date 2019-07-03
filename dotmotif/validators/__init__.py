#!/usr/bin/env python3
import abc

import networkx as nx


class Validator(abc.ABC):

    @abc.abstractmethod
    def validate(self) -> bool:
        ...


class NeuronConnectomeValidator(Validator):
    class NeuronConnectomeValidatorError(Exception):
        pass

    def __init__(self, g: nx.Graph) -> None:
        self.g = g

    def validate(self) -> bool:
        """
        Return True if valid.

        Raises NeuronConnectomeValidatorError if invalid.
        """
        return True


class DisagreeingEdgesValidatorError(Exception):
    pass


class DisagreeingEdgesValidator(Validator):
    def __init__(self) -> None:
        pass

    def validate(self, g: nx.Graph, u, v, type=None, exists: bool = True) -> bool:
        """
        Return True if valid.

        Raises DisagreeingEdgesValidatorError if invalid.
        """
        edges = g.edges(u, data=True)
        for u_, v_, attrs in edges:
            if u_ == u and v_ == v and exists != attrs["exists"]:
                raise DisagreeingEdgesValidatorError(
                    f"Trying to add <{u}-{v} exists={exists}> but "
                    f"<{u_}-{v_} exists={attrs['exists']}> already in motif."
                )
        return True
