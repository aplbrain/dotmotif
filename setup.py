#!/usr/bin/env python3

import os
from distutils.core import setup

import dotmotif

"""
git tag {VERSION}
git push --tags
python setup.py sdist upload -r pypi
"""

VERSION = dotmotif.__version__

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
        'numpy'
    ],
)
