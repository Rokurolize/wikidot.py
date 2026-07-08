# wikidot.py

[![Check Code Quality](https://github.com/Rokurolize/wikidot.py/actions/workflows/check_code_quality.yml/badge.svg?branch=main)](https://github.com/Rokurolize/wikidot.py/actions/workflows/check_code_quality.yml?query=branch%3Amain)
[![Codecov](https://codecov.io/gh/Rokurolize/wikidot.py/branch/main/graph/badge.svg)](https://codecov.io/gh/Rokurolize/wikidot.py)
[![CodeRabbit Reviews](https://img.shields.io/coderabbit/prs/github/Rokurolize/wikidot.py.svg?label=CodeRabbit%20Reviews)](https://coderabbit.ai)
[![Ask DeepWiki](https://deepwiki.com/badge.svg?repository=Rokurolize/wikidot.py)](https://deepwiki.com/Rokurolize/wikidot.py)

This repository is Rokurolize's fork of [ukwhatn/wikidot.py](https://github.com/ukwhatn/wikidot.py).
It is used for fork-local development, validation, and review support; upstream project links below describe the original `wikidot.py` package and documentation.

A Python library for easily interacting with Wikidot sites.

## Key Features

- Retrieve and manipulate sites, pages, users, forums, and more
- Create, edit, and delete pages
- Get, create, and reply to forum threads
- User management and site membership
- Send and receive private messages
- Supports both no-login features and authenticated features

## Installation

```bash
pip install wikidot
```

## Basic Usage

```python
import wikidot

# Use without login
client = wikidot.Client()

# Get site and page information
site = client.site.get("scp-jp")
page = site.page.get("scp-173")

print(f"Title: {page.title}")
print(f"Rating: {page.rating}")
print(f"Author: {page.created_by.name}")
```

## Documentation

For detailed usage, API reference, and examples, please see the upstream documentation:

**[Upstream Documentation](https://ukwhatn.github.io/wikidot.py/)**

- [Installation](https://ukwhatn.github.io/wikidot.py/installation.html)
- [Quickstart](https://ukwhatn.github.io/wikidot.py/quickstart.html)
- [Examples](https://ukwhatn.github.io/wikidot.py/examples.html)
- [API Reference](https://ukwhatn.github.io/wikidot.py/reference/index.html)

## Building Documentation

To build the documentation locally:

```bash
# Install packages required for documentation generation
make docs-install

# Build the documentation
make docs-build

# View documentation on local server (optional)
make docs-serve
```

## Contribution

- [Upstream roadmap](https://ukwhatn.notion.site/wikidot-py-roadmap?pvs=4)
- [Upstream issues](https://github.com/ukwhatn/wikidot.py/issues)
