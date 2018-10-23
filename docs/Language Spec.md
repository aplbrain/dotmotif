A -> B
B -> C | C.type == "excitatory"


# These are the same:
C !> D | -.type != "excitatory"
C !+ D
C ![excitatory] D
