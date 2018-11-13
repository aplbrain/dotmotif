#!/usr/bin/env python3

import os
from distutils.core import setup

"""
git tag {VERSION}
git push --tags
python setup.py sdist upload -r pypi
"""

VERSION = "0.3.0"

setup(
    name="dotmotif",
    version=VERSION,
    author="Jordan Matelsky",
    author_email="jordan.matelsky@jhuapl.edu",
    description=("dotmotif"),
    license="ISC",
    keywords=[
        "graph",
        "motif"
    ],
    url="https://github.com/aplbrain/dotmotif/tarball/" + VERSION,
    packages=['dotmotif'],
    scripts=[
        #  'scripts/'
    ],
    classifiers=[],
    install_requires=[
        'networkx',
        'numpy',
        'lark-parser',
        'docker',
        'pandas',
        'py2neo',
        'dask[dataframe]'
    ],
)
