from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import dotmotif


class Executor:
    ...

    def find(self, motif: 'dotmotif', limit: int = None):
        ...
