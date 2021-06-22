<p align="center">
  <img align="center" src="https://user-images.githubusercontent.com/693511/117350563-b58b9900-ae7a-11eb-83ce-9f5f9213145e.png" / width="25%">
  <h1 align="center" fontsize="2em">d o t m o t i f</h1>
</p>
<p align="center">Find graph motifs using intuitive notation</p>

<p align="center">
<a href="https://pypi.org/project/dotmotif/"><img alt="PyPI" src="https://img.shields.io/pypi/v/dotmotif?style=for-the-badge"></a>
<a href="https://bossdb.org/tools/DotMotif"><img src="https://img.shields.io/badge/Pretty Dope-👌-00ddcc.svg?style=for-the-badge" /></a>
<a href="https://bossdb.org/tools/DotMotif"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge" /></a>
<a href="https://codecov.io/gh/aplbrain/dotmotif"><img alt="Codecov" src="https://img.shields.io/codecov/c/github/aplbrain/dotmotif?style=for-the-badge"></a>
</p>

---

DotMotif is a library that identifies subgraphs or motifs in a large graph. It looks like this:

```yml
# Look for all motifs of the form,

# Neuron A excites B:
A -> B [type = "excitatory"]
# ...and B inhibits C:
B -> C [type = "inhibitory"]
```

Or like this:

```yml
TwitterInfluencer(person) {
    # An influencer has more than a million
    # followers and is verified.
    person.followers > 1000000
    person.verified = true
}

InfluencerAwkward(person1, person2) {
    # Two people who are both influencers...
    TwitterInfluencer(person1)
    TwitterInfluencer(person2)
    # ...where one follows the other, but...
    person1 -> person2
    # ...the other doesn't follow back
    person2 !> person1
}

# Search for all awkward twitter influencer
# relationships in the dataset:
InfluencerAwkward(X, Y)
```

# Get Started

> To follow along in an interactive Binder without installing anything, launch a Jupyter Notebook here:
>
> [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gist/j6k4m8/7da63dc9c049c4263fc2749d4ce880cd#file-get-started-dotmotif-ipynb/HEAD)

If you have [DotMotif](https://github.com/aplbrain/dotmotif/wiki/Installation), a NetworkX graph, and a curious mind, you already have everything you need to start using DotMotif:

```python
from dotmotif import Motif, GrandIsoExecutor

executor = GrandIsoExecutor(graph=my_networkx_graph)

triangle = Motif("""
A -> B
B -> C
C -> A
""")

results = executor.find(triangle)
```

# Parameters

You can also pass optional parameters into the constructor for the `dotmotif` object. Those arguments are:

| Argument                | Type, Default   | Behavior                                                                                                                                                                       |
| ----------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ignore_direction`      | `bool`: `False` | Whether to disregard direction when generating the database query                                                                                                              |
| `limit`                 | `int`: `None`   | A limit (if any) to impose on the query results                                                                                                                                |
| `enforce_inequality`    | `bool`: `False` | Whether to enforce inequality; in other words, whether two nodes should be permitted to be aliases for the same node. For example, in `A->B->C`; if `A!=C`, then set to `True` |
| `exclude_automorphisms` | `bool`: `False` | Whether to return only a single example for each detected automorphism. See more in [the documentation](https://github.com/aplbrain/dotmotif/wiki/Automorphisms)               |

For more details on how to write a query, see [Getting Started](https://github.com/aplbrain/dotmotif/wiki/Getting-Started).

---

# Citing

If this tool is helpful to your research, please consider citing it with:

```bibtex
# https://doi.org/10.1038/s41598-021-91025-5
@article{Matelsky_Motifs_2021, 
    title={{DotMotif: an open-source tool for connectome subgraph isomorphism search and graph queries}},
    volume={11}, 
    ISSN={2045-2322}, 
    url={http://dx.doi.org/10.1038/s41598-021-91025-5}, 
    DOI={10.1038/s41598-021-91025-5}, 
    number={1}, 
    journal={Scientific Reports}, 
    publisher={Springer Science and Business Media LLC}, 
    author={Matelsky, Jordan K. and Reilly, Elizabeth P. and Johnson, Erik C. and Stiso, Jennifer and Bassett, Danielle S. and Wester, Brock A. and Gray-Roncal, William},
    year={2021}, 
    month={Jun}
}
```
