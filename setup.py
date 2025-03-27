from setuptools import setup, find_packages

setup(
    name="skill-similarity-engine",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "matplotlib>=3.4.0",
        "scikit-learn>=0.24.0",
    ],
    python_requires=">=3.8",
) 