#!/usr/bin/env python

from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    readme = f.read()

setup(
    name='mqtt-py-wrapper',
    version='0.0.1a0',
    description='MQTT client simplification wrapper',
    long_description=readme,
    long_description_content_type="text/markdown",
    author='Thomas Finstad Larsen',
    url='https://github.com/basefarm/mqtt-py-wrapper.git',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
        'Topic :: Communications',
        'Topic :: Internet',
    ],
    install_requires=['setuptools==57.4.0', 'paho-mqtt==1.5.1'],
    test_suite='tests',
    tests_require=['pytest'],
    setup_requires=[],
    extras_require={},
    python_requires=">=3.6",
)
