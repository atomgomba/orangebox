#!/usr/bin/env python3
from setuptools import setup

import orangebox

setup(
    name="orangebox",
    version=orangebox.__version__,
    packages=["orangebox"],
    scripts=["scripts/bb2csv", "scripts/bbsplit", "scripts/bb2gpx"],
    author="Károly Kiripolszky",
    author_email="karcsi@ekezet.com",
    description="A Cleanflight/Betaflight blackbox log parser written in Python 3",
    keywords="blackbox cleanflight betaflight",
    url="https://github.com/atomgomba/orangebox",
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
        "Topic :: System :: Archiving :: Compression",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    python_requires=">=3.5"
)
