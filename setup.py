#!/usr/bin/env python3

from setuptools import setup, find_packages # type: ignore
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
      author='AIPlan4EU Organization',
      author_email='aiplan4eu@fbk.eu',
      url='https://aiplan4eu.fbk.eu/',
      packages=find_packages(),
      include_package_data=True,
      install_requires=['tarski @ git+https://github.com/aig-upf/tarski.git@ebfda1c13ac908904d5b74587971cc7149e73d85#egg=tarski[arithmetic]'],
      license='APACHE'
     )
