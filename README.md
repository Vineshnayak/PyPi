# Python Packages Collection

A collection of custom Python libraries and package codebases published through PyPI.

## Overview

This repository serves as a centralized workspace for developing, maintaining, and distributing Python packages. Each package is an independent project with its own source code, configuration, dependencies, and release workflow.

## Available Packages

| Package  | Description                                       | Status |
| -------- | ------------------------------------------------- | ------ |
| PwdScore | Password strength evaluation and scoring utility. | Active |

Additional packages may be added over time.

## Installation

```bash
git clone https://github.com/Vineshnayak/PyPi.git
cd PyPi
```

Navigate to a package:

```bash
cd PwdScore
```

Install locally:

```bash
pip install -e .
```

## Development

Run tests:

```bash
pytest
```

Build distributions:

```bash
python -m build
```

Publish to PyPI:

```bash
twine upload dist/*
```

## License

See the LICENSE file for licensing information.
