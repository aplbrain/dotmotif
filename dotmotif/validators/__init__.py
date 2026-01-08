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
                lower_bounds = []  # (value, strict)
                upper_bounds = []  # (value, strict)

                def op_repr(val, strict: bool, lower: bool) -> str:
                    return (
                        (">" if strict else ">=")
                        if lower
                        else ("<" if strict else "<=")
                    ) + str(val)

                for op, values in ops.items():
                    if op in eq_ops:
                        eq_values.extend(values)
                    elif op in neq_ops:
                        neq_values.extend(values)
                    elif op in {">", ">=", "<", "<="}:
                        if op in {">", ">="}:
                            lower_bounds.extend([(v, op == ">") for v in values])
                        else:
                            upper_bounds.extend([(v, op == "<") for v in values])

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

                # Range consistency: combine lower/upper bounds and equality
                if lower_bounds:
                    lower_val, lower_strict = max(lower_bounds, key=lambda t: t[0])
                else:
                    lower_val, lower_strict = None, False

                if upper_bounds:
                    upper_val, upper_strict = min(upper_bounds, key=lambda t: t[0])
                else:
                    upper_val, upper_strict = None, False

                if eq_values:
                    eq_val = eq_values[0]
                    # Equality must satisfy bounds
                    if lower_val is not None:
                        if eq_val < lower_val or (eq_val == lower_val and lower_strict):
                            raise self.ConstraintCollisionError(
                                f"Equality {node}.{attr}={eq_val} violates lower bound {op_repr(lower_val, lower_strict, lower=True)}"
                            )
                    if upper_val is not None:
                        if eq_val > upper_val or (eq_val == upper_val and upper_strict):
                            raise self.ConstraintCollisionError(
                                f"Equality {node}.{attr}={eq_val} violates upper bound {op_repr(upper_val, upper_strict, lower=False)}"
                            )
                else:
                    # Pure range: ensure non-empty interval
                    if lower_val is not None and upper_val is not None:
                        if lower_val > upper_val or (
                            lower_val == upper_val and (lower_strict or upper_strict)
                        ):
                            raise self.ConstraintCollisionError(
                                f"Impossible bounds on {node}.{attr}: {op_repr(lower_val, lower_strict, lower=True)} and {op_repr(upper_val, upper_strict, lower=False)}"
                            )

        # Dynamic node constraints (cross-node attribute comparisons)
        for node, constraints in motif.list_dynamic_node_constraints().items():
            for attr, ops in constraints.items():
                lowers = []  # (other_node, other_attr, op)
                uppers = []
                for op, targets in ops.items():
                    for other_node, other_attr in targets:
                        if op in {">", ">="}:
                            lowers.append((other_node, other_attr, op))
                        elif op in {"<", "<="}:
                            uppers.append((other_node, other_attr, op))

                for on, oa, lop in lowers:
                    for un, ua, uop in uppers:
                        if (on, oa) == (un, ua):
                            # Only safe case is non-strict sandwich >= / <= on the same target
                            if not (lop == ">=" and uop == "<="):
                                raise self.ConstraintCollisionError(
                                    f"Impossible dynamic bounds on {node}.{attr} with {on}.{oa}: {lop} and {uop}"
                                )

        return True
