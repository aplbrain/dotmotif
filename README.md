<p align="center">
  <img align="center" src="./logo.png" / width="25%">
  <h1 align="center" fontsize="2em">d o t m o t i f</h1>
</p>
<p align="center">Find graph motifs using intuitive notation</p>

<p align="center">
<a href="https://pypi.org/project/dotmotif/"><img alt="PyPI" src="https://img.shields.io/pypi/v/dotmotif?style=for-the-badge"></a>
<a href="https://bossdb.org/tools/DotMotif"><img src="https://img.shields.io/badge/Pretty Dope-👌-00ddcc.svg?style=for-the-badge" /></a>
<a href="https://bossdb.org/tools/DotMotif"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge" /></a>
</p>

# Usage

## Writing a motif

You can currently write motifs in dotmotif form, which is a DSL that specializes in subgraph query notation.

`threecycle.motif`

```dot
# A excites B
A -> B [type = "excitatory"]
# B inhibits C
B -> C [type = "inhibitory"]
```

## Ingesting the motif into dotmotif

```python
import dotmotif

dm = dotmotif.Motif("threecycle.motif")
```

## Inline code in Python

Alternatively, you can inline your motif in the python code when creating your `dotmotif` object:

```python
dm = dotmotif.Motif("""
# A excites B
A -> B [type = "excitatory"]
# B inhibits C
B -> C [type = "inhibitory"]
""")
```

## Parameters

You can also pass optional parameters into the constructor for the `dotmotif` object. Those arguments are:

| Argument                | Type, Default   | Behavior                                                                                                                                                                       |
| ----------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ignore_direction`      | `bool`: `False` | Whether to disregard direction when generating the database query                                                                                                              |
| `limit`                 | `int`: `None`   | A limit (if any) to impose on the query results                                                                                                                                |
| `enforce_inequality`    | `bool`: `False` | Whether to enforce inequality; in other words, whether two nodes should be permitted to be aliases for the same node. For example, in `A->B->C`; if `A!=C`, then set to `True` |
| `exclude_automorphisms` | `bool`: `False` | Whether to return only a single example for each detected automorphism. See more in [the documentation](https://github.com/aplbrain/dotmotif/wiki/Automorphisms)                                                 |

For more details on how to write a query, see [Getting Started](https://github.com/aplbrain/dotmotif/wiki/Getting-Started).

# Citing

If this tool is helpful to your research, please consider citing it with:

```bibtex
# https://www.biorxiv.org/content/10.1101/2020.06.08.140533v2
@article{matelsky_2020_dotmotif,
    doi = {10.1101/2020.06.08.140533},
    url = {https://www.biorxiv.org/content/10.1101/2020.06.08.140533v2},
    year = 2020,
    month = {june},
    publisher = {BiorXiv},
    author = {Matelsky, Jordan K. and Reilly, Elizabeth P. and Johnson,Erik C. and Wester, Brock A. and Gray-Roncal, William},
    title = {{Connectome subgraph isomorphisms and graph queries with DotMotif}},
    journal = {BiorXiv}
}
```
