"""Setup script for Signal Hub."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="signal-hub",
    version="0.1.0",
    author="Signal Hub Contributors",
    author_email="maintainers@signalhub.ai",
    description="Intelligent developer assistant that extends Claude's context through MCP+RAG",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wespiper/signal-hub",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "chromadb>=0.4.0",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "pyyaml>=6.0",
        "rich>=13.0.0",
        "typer>=0.9.0",
        "numpy>=1.24.0",
        "aiofiles>=23.0.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.25.0",
        "tenacity>=8.2.0",
        "psutil>=5.9.0",
        "cryptography>=41.0.0",
        "bcrypt>=4.0.0",
        "questionary>=2.0.0",
        "watchdog>=3.0.0",
        "tree-sitter>=0.21.0",
        "tree-sitter-python>=0.21.0",
        "tree-sitter-javascript>=0.21.0",
        "tree-sitter-typescript>=0.21.0",
        "aiohttp>=3.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "pro": [
            "anthropic>=0.3.0",
            "scikit-learn>=1.3.0",
            "pandas>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "signal-hub=signal_hub.cli.main:app",
        ],
    },
)