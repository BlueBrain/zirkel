import os
import sys
from setuptools import find_packages
from setuptools import setup

__version__ = "0.0.1"


if __name__ == "__main__":
    setup(
        name="zirkel",
        version=__version__,
        include_package_data=True,
        packages=find_packages(),
        python_requires="~=3.6",
        install_requires=[
            "numpy",
            "anytree",
        ],
        zip_safe=False,
    )
