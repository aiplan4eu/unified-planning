#!/usr/bin/env python3

from setuptools import setup, find_packages  # type: ignore
import unified_planning


long_description = "Unified Planning: A library that makes it easy to formulate planning problems and to invoke automated planners."

setup(
    name="unified_planning",
    version=unified_planning.__version__,
    description="Unified Planning Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AIPlan4EU Project",
    author_email="aiplan4eu@fbk.eu",
    url="https://www.aiplan4eu-project.eu",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=["pyparsing", "networkx", "ConfigSpace"],
    extras_require={
        "dev": ["tarski[arithmetic]", "pytest", "pytest-cov", "mypy"],
        "grpc": ["grpcio", "grpcio-tools", "grpc-stubs"],
        "tarski": ["tarski[arithmetic]"],
        "pyperplan": ["up-pyperplan==1.0.0"],
        "tamer": ["up-tamer==1.0.0"],
        "enhsp": ["up-enhsp==0.0.19"],
        "fast-downward": ["up-fast-downward==0.3.1"],
        "lpg": ["up-lpg==0.0.7"],
        "fmap": ["up-fmap==0.0.7"],
        "mabfws": ["up-ma-bfws==0.0.4"],
        "aries": ["up-aries>=0.0.8"],
        "symk": ["up-symk>=0.0.3"],
        "engines": [
            "tarski[arithmetic]",
            "up-pyperplan==1.0.0.1.dev1",
            "up-tamer==1.0.0.1.dev1",
            "up-enhsp==0.0.19",
            "up-fast-downward==0.3.1",
            "up-lpg==0.0.7",
            "up-fmap==0.0.7",
            "up-ma-bfws==0.0.4",
            "up-aries>=0.0.8",
            "up-symk>=0.0.3",
        ],
        "plot": [
            "plotly",
            "matplotlib==3.7.3",
            "kaleido",
            "pygraphviz",
            "graphviz",
            "pandas",
        ],
    },
    license="APACHE",
    keywords="planning logic STRIPS RDDL",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "up = unified_planning.cmd.up:main",
        ],
    },
)
