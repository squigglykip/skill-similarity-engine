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
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'skill-similarity=skill_similarity_engine.cli.main:main',
            'hris-analysis=skill_similarity_engine.hris_adapter.cli:main',
        ],
    },
    author="NAB",
    author_email="info@nab.com",
    description="Skill Similarity Engine for workforce analytics",
    keywords="skills, similarity, workforce, analytics",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
) 