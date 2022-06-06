#!/usr/bin/env python3

import os
import io
from setuptools import find_packages, setup

"""
git tag {VERSION}
git push --tags
python setup.py sdist
twine upload dist/*
"""

VERSION = "0.12.0"

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
        "networkx>2.4",
        "numpy",
        "lark-parser",
        "pandas",
        "grandiso>=2.0.0",
    ],
    extras_require={
        "neo4j": [
            "docker",
            "tamarind>=0.1.5",
            "py2neo",
        ],
        "neuprint": [
            "neuprint-python",
        ],
    },
    include_package_data=True,
)
