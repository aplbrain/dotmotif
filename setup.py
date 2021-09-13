#!/usr/bin/env python3

import os
import io
from setuptools import find_packages, setup, Command

"""
git tag {VERSION}
git push --tags
python setup.py sdist
twine upload dist/*
"""

VERSION = "0.9.2"

here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

setup(
    name="dotmotif",
    version=VERSION,
    author="Jordan Matelsky",
    author_email="jordan.matelsky@jhuapl.edu",
    description=("Find graph motifs using simple, intuitive notation"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache 2.0",
    keywords=["graph", "motif"],
    url="https://github.com/aplbrain/dotmotif/tarball/" + VERSION,
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    classifiers=[],
    install_requires=[
        "networkx",
        "numpy",
        "lark-parser",
        "docker",
        "pandas",
        "py2neo",
        "dask[dataframe]",
        "tamarind>=0.1.5",
        "neuprint-python",
        "grandiso<2.0.0",
    ],
    include_package_data=True,
)
