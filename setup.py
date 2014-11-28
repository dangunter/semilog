#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Semi-structured logging for Python.
"""
import semilog

__author__ = 'Dan Gunter <dkgunter@lbl.gov>'
__date__ = '2014-11-27'

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
    readme = f.read()

packages = [
    'semilog',
]

package_data = {
}

requires = []
with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
    for line in f:
        requires.append(line.strip())

classifiers = [
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

setup(
    name='semilog',
    version=semilog.__version__,
    description='Semi-structured logging library.',
    long_description=readme,
    packages=packages,
    package_data=package_data,
    install_requires=requires,
    author=semilog.__author__.split()[0],
    author_email=semilog.__author__.split()[1],
    url='https://github.com/dangunter/semilog',
    license='MIT',
    classifiers=classifiers,
)
