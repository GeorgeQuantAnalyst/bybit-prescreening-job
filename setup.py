import os

from setuptools import setup, find_packages

NAME = "bybit-prescreening-job"
DESCRIPTION = "Application for find buyers/sellers imbalances by Heikin Ashi candle sticks charts on Bybit futures"
AUTHOR = "GeorgeQuantAnalyst"
URL = ""
VERSION = None

about = {}

with open(
        os.path.join(os.path.dirname(__file__), "requirements.txt"), "r"
) as fh:
    requirements = fh.readlines()

root = os.path.abspath(os.path.dirname(__file__))

if not VERSION:
    with open(os.path.join(root, "bybit_prescreening_job", "__version__.py")) as f:
        exec(f.read(), about)
else:
    about["__version__"] = VERSION

setup(
    name=NAME,
    version=about["__version__"],
    license="BSD 2",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    AUTHOR=AUTHOR,
    url=URL,
    keywords=["Algo-trading", "Bybit"],
    install_requires=[req for req in requirements],
    packages=find_packages(exclude=("tests",)),
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
)
