from setuptools import setup, find_packages

setup(
    name="group-theory-stock-factor",
    version="1.0.0",
    description="Market state factor based on graph automorphism group analysis",
    author="eluckydog",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "networkx>=2.6",
        "scikit-learn>=1.0",
        "matplotlib>=3.4.0",
    ],
    python_requires=">=3.8",
    license="MIT",
)
