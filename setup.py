#!/usr/bin/env python

import setuptools

import klempner

setuptools.setup(
    name='klempner',
    version=klempner.version,
    description='Construct service request URLs',
    long_description=open('README.rst').read(),
    url='https://klempner.readthedocs.io/',
    author='Dave Shawley',
    author_email='daveshawley@gmail.com',
    project_urls={
        'Builds': 'https://circleci.com/gh/dave-shawley/klempner',
        'Documentation': 'https://klempner.readthedocs.io/',
        'Download': 'https://pypi.org/project/klempner/',
        'Quality Reports': ('https://sonarcloud.io/dashboard'
                            '?id=dave-shawley_klempner'),
        'Source Code': 'https://github.com/dave-shawley/klempner',
    },
    packages=['klempner'],
    install_requires=[
        'cachetools==3.1.0',
        'requests==2.21.0',
    ],
    tests_require=[
        'coverage==4.5.3',
        'mock==1.0.1; python_version<"3"',
    ],
    extras_require={
        'dev': [
            'coverage==4.5.3',
            'flake8==3.7.7',
            'mock==1.0.1; python_version<"3"',
            'tox==3.8.6',
            'yapf==0.26.0',
        ],
        'docs': [
            'sphinx==2.0.1',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries',
    ],
)
