#!/usr/bin/env python3

from setuptools import setup, find_packages
import upf


long_description=\
"""============================================================
 UPF: A library that unifies planning frameworks
 ============================================================
    Insert long description here
"""

setup(name='upf',
      version=upf.__version__,
      description='Unified planning framework',
      author='UPF Team',
      author_email='info@upf.com',
      url='https://aiplan4eu.fbk.eu/',
      packages=find_packages(),
      include_package_data=True,
      license='APACHE'
     )
