#!/usr/bin/env python
from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


version = '0.2.8'

install_requires = [
    'threadpool',
    'pyyaml',
]


setup(name='python-dnslb',
    version=version,
    description="Simple Python DNS load balancer for geodns",
    long_description=README + '\n\n' + NEWS,
    classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords='cdn dlb',
    author='Leif Johansson',
    author_email='leifj@mnt.se',
    url='http://blogs.mnt.se',
    license='BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    entry_points={
        'console_scripts':
            ['dnslb=dnslb:main']
    },
    requires=install_requires
)
