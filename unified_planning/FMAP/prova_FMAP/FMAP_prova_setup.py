#!/usr/bin/env python3
import subprocess

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
import os
import urllib
import shutil


ENHSP_dst = './up_enhsp/ENHSP'
ENHSP_PUBLIC = 'ENHSP-Public'
COMPILE_CMD = './compile'
ENHSP_TAG = 'enhsp20-0.9.2'
ENHSP_REPO = 'https://gitlab.com/enricos83/ENHSP-Public'

long_description = \
    """============================================================
    UP_ENHSP
 ============================================================
"""


def install_ENHSP():
    subprocess.run(['git', 'clone', '-b', ENHSP_TAG, ENHSP_REPO])
    shutil.move(ENHSP_PUBLIC, ENHSP_dst)
    curr_dir = os.getcwd()
    os.chdir(ENHSP_dst)
    subprocess.run(COMPILE_CMD)
    os.chdir(curr_dir)


class InstallENHSP(build_py):
    """Custom install command."""

    def run(self):
        install_ENHSP()
        build_py.run(self)


class InstallENHSPdevelop(develop):
    """Custom install command."""

    def run(self):
        install_ENHSP()
        develop.run(self)


setup(name='up_enhsp',
      version='0.0.1',
      description='up_enhsp',
      author='UNIBS Team',
      author_email='enrico.scala@unibs.it',
      packages=['up_enhsp'],
      package_data={
          "": ["ENHSP/enhsp.jar","ENHSP/libs/*"],
      },
      cmdclass={
          'build_py': InstallENHSP,
          'develop': InstallENHSPdevelop,
      },
      license='APACHE')