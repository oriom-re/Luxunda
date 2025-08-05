
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="luxdb",
    version="0.1.0",
    author="LuxDB Team",
    author_email="contact@luxdb.dev",
    description="Genetic Database Library - Nie relacja. Nie dokument. Ewolucja danych.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/luxdb",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/luxdb/issues",
        "Documentation": "https://github.com/yourusername/luxdb/blob/main/README.md",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    package_dir={"": "."},
    packages=find_packages(where=".", exclude=["tests", "legacy", "static", "examples"]),
    python_requires=">=3.11",
    install_requires=[
        "asyncpg>=0.28.0",
        "ulid-py>=1.1.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
        ],
        "ai": [
            "openai>=1.0.0",
            "numpy>=1.24.0",
            "scikit-learn>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "luxdb-init=luxdb.cli:init_database",
            "luxdb-migrate=luxdb.cli:migrate",
        ],
    },
    include_package_data=True,
    package_data={
        "luxdb": ["templates/*.sql", "migrations/*.sql"],
    },
)
