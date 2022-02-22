#!/usr/bin/env python3

from setuptools import setup, find_packages # type: ignore
import unified_planning


long_description=\
"""============================================================
 Unified planning: A library that unifies planning frameworks
 ============================================================
    Insert long description here
"""

setup(name='unified_planning',
      version=unified_planning.__version__,
      description='Unified planning framework',
      author='AIPlan4EU Organization',
      author_email='aiplan4eu@fbk.eu',
      url='https://www.aiplan4eu-project.eu',
      packages=find_packages(),
      include_package_data=True,
      install_requires=['pyparsing>=3.0.0', 'tarski @ git+https://github.com/aig-upf/tarski.git@ebfda1c13ac908904d5b74587971cc7149e73d85#egg=tarski[arithmetic]'],
      license='APACHE'
     )
