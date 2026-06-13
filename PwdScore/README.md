# pwdscore

A Python package to score password strength based on various criteria (length, uppercase letters, lowercase letters, digits, and special characters).

## Installation

```bash
pip install pwdscore
```

## Usage

```python
from pwdscore import score, check

# Get a numeric score from 0 to 100
print(score("Password123!"))  # Output: 87 (or similar depending on rules)

# Get a string rating (Weak, Medium, Strong)
print(check("Password123!"))  # Output: Strong
```

## Development

To build the package:

```bash
python -m build
```

To run tests:

```bash
pytest
```
