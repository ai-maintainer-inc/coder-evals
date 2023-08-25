#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "Click>=7.0",
    "agent-marketplace-sdk==0.1.3",
    "docker>=4.2.2",
    "aider-chat>=0.12.0",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Douglas Schonholtz",
    author_email="douglas@ai-maintainer.com",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="AI Maintainer Agent Harness for our benchmarking and Marketplace API and platform",
    entry_points={
        "console_scripts": [
            "agent_harness=agent_harness.cli:main",
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="agent_harness",
    name="agent_harness",
    packages=find_packages(include=["agent_harness", "agent_harness.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/dschonholtz/agent_harness",
    version="0.1.0",
    zip_safe=False,
)
