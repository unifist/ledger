#!/usr/bin/env python

import os
from setuptools import setup

version = os.environ.get("BUILD_VERSION")

if version is None:
    with open("VERSION", "r") as version_file:
        version = version_file.read().strip()

setup(
    name="ledger",
    version=version,
    package_dir = {'': 'api/lib'},
    py_modules = ['ledger'],
    install_requires=[
        'relations-rest==0.5.0'
    ]
)
