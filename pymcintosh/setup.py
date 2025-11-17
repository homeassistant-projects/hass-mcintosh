#!/usr/bin/env python

import sys

if sys.version_info < (3, 10):
    raise RuntimeError('This package requires Python 3.10+')

VERSION = '0.1.0'

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='pymcintosh',
    version=VERSION,
    description='Python library for controlling McIntosh MX160/MX170/MX180 processors',
    author='Ryan Snodgrass',
    url='https://github.com/homeassistant-community/hass-mcintosh',
    packages=['pymcintosh'],
    install_requires=[
        'pyserial>=3.5',
        'pyserial-asyncio>=0.6',
    ],
    python_requires='>=3.10',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
)
