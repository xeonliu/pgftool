#!/usr/bin/env python3
"""Setup script for pgftool."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pgftool",
    version="1.0.0",
    author="xeonliu",
    description="PGF font tools for PSP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "Pillow>=8.0.0",
        "freetype-py>=2.3.0",
    ],
    entry_points={
        "console_scripts": [
            "dump_pgf=pgftool.dump_pgf:main",
            "mix_pgf=pgftool.mix_pgf:main",
            "ttf_pgf=pgftool.ttf_to_pgf:main",
        ],
    },
)
