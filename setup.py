#!/usr/bin/env python3

import os
from setuptools import find_packages, setup, Command

"""
git tag {VERSION}
git push --tags
python setup.py sdist upload -r pypi
"""

VERSION = "0.4.2"

setup(
    name="dotmotif",
    version=VERSION,
    author="Jordan Matelsky",
    author_email="jordan.matelsky@jhuapl.edu",
    description=("dotmotif"),
    license="ISC",
    keywords=["graph", "motif"],
    url="https://github.com/aplbrain/dotmotif/tarball/" + VERSION,
    packages=find_packages(
        exclude=["tests", "*.tests", "*.tests.*", "tests.*"]
    ),
    scripts=[
        #  'scripts/'
    ],
    classifiers=[],
    install_requires=[
        "networkx",
        "numpy",
        "lark-parser",
        "docker",
        "pandas",
        "py2neo",
        "dask[dataframe]",
        "tamarind",
    ],
)
