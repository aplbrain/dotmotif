#!/usr/bin/env python3
import abc
from typing import Optional

import networkx as nx


class Validator(abc.ABC):
    @abc.abstractmethod
    def validate(self, *args, **kwargs) -> bool: ...

    def validate_motif(self, motif) -> bool:
        """Motif-level hook"""
        return True


class DisagreeingEdgesValidatorError(Exception):
    pass


class DisagreeingEdgesValidator(Validator):
    def __init__(self) -> None:
        pass

    def validate(
        self, g: nx.Graph, u, v, type=None, exists: bool = True, **kwargs
    ) -> bool:
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


class ImpossibleConstraintValidator(Validator):
    class ConstraintCollisionError(ValueError):
        pass

    def validate(self, *args, **kwargs) -> bool:
        """Edge-level hook (no-op) to satisfy Validator interface."""
        return True

    def validate_motif(self, motif) -> bool:
        """Ensure node constraints remain consistent after automorphism propagation."""

        eq_ops = {"=", "=="}
        neq_ops = {"!=", "<>"}

        for node, constraints in motif.list_node_constraints().items():
            for attr, ops in constraints.items():
                eq_values = []
                neq_values = []

                for op, values in ops.items():
                    if op in eq_ops:
                        eq_values.extend(values)
                    elif op in neq_ops:
                        neq_values.extend(values)

                # Multiple distinct equality values collide
                if len(set(eq_values)) > 1:
                    raise self.ConstraintCollisionError(
                        f"Conflicting equality constraints on {node}.{attr}: {set(eq_values)}"
                    )

                # Equality vs inequality of the same value collides
                if eq_values and any(v in eq_values for v in neq_values):
                    raise self.ConstraintCollisionError(
                        f"Conflicting equality/inequality constraints on {node}.{attr}: eq={eq_values}, neq={neq_values}"
                    )

        return True
