# FaultSnap

### 1. What is FaultSnap?
FaultSnap is a black-box recorder for Python applications.
When your program crashes, FaultSnap captures the execution context, stores it in a portable `.faultsnap` archive, and allows another developer to inspect the crash without reproducing it.

### 2. Why FaultSnap Exists
When an exception occurs, Python provides a standard traceback. However, tracebacks only give you the file and line number. They don't tell you the state of variables at the time of the crash.

```python
user = None
print(user.name) # AttributeError: 'NoneType' object has no attribute 'name'
```

Why is `user` None? What were the variables leading up to this? With FaultSnap, you can inspect every local variable, frame by frame, exactly as it was when the crash occurred.

### 3. Installation
```bash
pip install faultsnap
```

To enable offline HTML report generation:
```bash
pip install faultsnap[html]
```

### 4. Quick Start
```python
import faultsnap

faultsnap.install()

1 / 0
```

Output:
```text
[FaultSnap] Crash captured. Saved to FaultSnaps/ZeroDivisionError/2026-06-13/1eaee423/crash_232934_1eaee423.faultsnap
```

### 5. How FaultSnap Works
1. **Capture**: Intercepts unhandled exceptions globally or via framework middleware.
2. **Serialize**: Traverses the execution stack safely, truncating large structures and handling circular references to prevent cascading failures.
3. **Mask**: Redacts sensitive data (like passwords, keys, and tokens) matching predefined or custom regex patterns.
4. **Fingerprint**: Computes a unique SHA-256 hash based on the execution path to group identical crashes.
5. **Package**: Generates a `.faultsnap` ZIP archive with manifest metadata and a standalone HTML report.
6. **Analyze**: Use the CLI to search, inspect, and visualize crashes from the repository.

### 6. Crash Repository Structure
FaultSnap organizes all crashes in a central `FaultSnaps/` directory to prevent cluttering your project root. The repository maintains an `index.json` to allow fast searching and a `latest/` folder pointing to the most recent crash.

```text
FaultSnaps/
├── index.json
├── latest/
│   ├── latest.faultsnap
│   └── latest.html
└── ZeroDivisionError/
    └── 2026-06-13/
        └── 1eaee423/
            ├── crash_232934.faultsnap
            ├── crash_232934.html
            └── metadata.json
```

### 7. Complete CLI Reference
Manage and analyze your crashes directly from the terminal.

#### `faultsnap list`
**Purpose**: Shows all stored crashes in a tabular view.
**Syntax**: `faultsnap list`
**Example Output**:
```text
Timestamp                Exception            Fingerprint
----------------------------------------------------------------
2026-06-13 23:29:34      ZeroDivisionError    1eaee423
2026-06-13 23:31:15      AttributeError       3abf9121
```

#### `faultsnap latest`
**Purpose**: Inspect the most recent crash.
**Syntax**: `faultsnap latest`
**Example**: Immediately displays the metadata and exception string for the crash in `FaultSnaps/latest/`.

#### `faultsnap search`
**Purpose**: Search the crash index by exception type or fingerprint.
**Syntax**: `faultsnap search <term>`
**Example**: `faultsnap search ZeroDivisionError` or `faultsnap search 1eaee423`

#### `faultsnap stats`
**Purpose**: Display repository statistics.
**Syntax**: `faultsnap stats`
**Example Output**:
```text
Total Crashes: 154
Unique Fingerprints: 23
Most Common Error: AttributeError
Oldest Crash: 2026-05-01
Newest Crash: 2026-06-13
```

#### `faultsnap clean`
**Purpose**: Remove expired reports based on the retention policy configured via `faultsnap.configure(max_days_to_keep=30)`.
**Syntax**: `faultsnap clean`

#### `faultsnap inspect`
**Purpose**: View high-level metadata and the raw traceback for a specific capsule.
**Syntax**: `faultsnap inspect <file>`
**Example**: `faultsnap inspect FaultSnaps/latest/latest.faultsnap`

#### `faultsnap stack`
**Purpose**: Render an interactive tree view of the call stack.
**Syntax**: `faultsnap stack <file>`

#### `faultsnap vars`
**Purpose**: View local variables for every execution frame.
**Syntax**: `faultsnap vars <file>`

#### `faultsnap env`
**Purpose**: View captured environment variables safely.
**Syntax**: `faultsnap env <file>`

#### `faultsnap fingerprint`
**Purpose**: Print the unique hash of the crash.
**Syntax**: `faultsnap fingerprint <file>`

#### `faultsnap diff`
**Purpose**: Compare metadata between two different crash files.
**Syntax**: `faultsnap diff <file1> <file2>`

#### `faultsnap html`
**Purpose**: Generate a standalone HTML dashboard for a specific capsule.
**Syntax**: `faultsnap html <file>`

### 8. HTML Reports
The HTML report provides an interactive diagnostic dashboard that operates completely offline. It features:
* **Search & Variable Filtering**: Quickly find specific variables across deep call stacks.
* **Stack Exploration**: Expand/collapse frames to view line-by-line context and local state.
* **Execution Graph**: A visual flow of the exception path via a bundled Mermaid.js graph.

### 9. Framework Integrations
FaultSnap provides explicit integration handlers for major frameworks.

**AsyncIO**
```python
import asyncio
from faultsnap.integrations.asyncio import install

async def main():
    install()
    # Async execution
```

**Multiprocessing**
```python
from faultsnap.integrations.multiprocessing import install
install()
```

**Flask**
```python
from flask import Flask
from faultsnap.integrations.flask import install

app = Flask(__name__)
install(app)
```

**FastAPI**
```python
from fastapi import FastAPI
from faultsnap.integrations.fastapi import install

app = FastAPI()
install(app)
```

**Django**
Add to `MIDDLEWARE` in `settings.py`:
```python
MIDDLEWARE = [
    'faultsnap.integrations.django.FaultSnapMiddleware',
]
```

**Streamlit**
```python
from faultsnap.integrations.streamlit import install
install()
```

**Pytest**
In `conftest.py`:
```python
pytest_plugins = ["faultsnap.integrations.pytest_plugin"]
```

### 10. Security Features
* **Secret Masking**: Automatically redacts values for keys containing terms like `password`, `secret`, `token`, `key`, and `auth`.
* **Safe Environment Capture**: Captures only benign OS variables (`PATH`, `OS`, `TERM`) by default to prevent accidental credential leaks.
* **Offline Operation**: FaultSnap operates strictly offline. It never transmits data externally and HTML reports embed all necessary dependencies.
* **HTML Escaping**: Strict Jinja2 autoescaping prevents XSS vulnerabilities in generated reports.

### 11. Performance
* **Depth Limits**: Traversal stops at a safe recursion depth (`max_depth=5`).
* **Truncation**: Lists and strings are truncated to prevent infinite evaluation and memory exhaustion (`max_items=50`).
* **Memory Protection**: A global persistent counter enforces a hard limit on the total number of objects processed (`max_total_items=10000`).

### 12. Architecture Overview
* **`core.py`**: Injects hooks into Python runtimes and extracts context from `f_locals`.
* **`serializer.py`**: Safely evaluates and truncates arbitrary Python objects into JSON-friendly formats.
* **`mask.py`**: Scans keys and redacts sensitive data using regex.
* **`fingerprint.py`**: Generates a unified SHA-256 hash representing the crash path.
* **`capsule.py`**: Compresses the payload into a `.faultsnap` ZIP archive.
* **`storage.py`**: Organizes artifacts into the hierarchical `FaultSnaps/` repository, updates indexes, and handles retention.
* **`html.py`**: Combines crash metadata with Jinja2 templates for interactive offline reports.
* **`cli.py`**: Powers the interactive terminal inspector.

### 13. FAQ

**Q: Why is my variable truncated?**
A: FaultSnap imposes strict bounds (`max_items`, `max_string_len`) to ensure the crash capturer never causes an Out-Of-Memory error itself. You can increase these via `faultsnap.configure()`.

**Q: Why are passwords masked?**
A: To prevent accidental exfiltration or logging of secrets in developer crash dumps.

**Q: How do I open a `.faultsnap` file?**
A: Use the FaultSnap CLI (`faultsnap inspect <file>`) or generate an HTML report (`faultsnap html <file>`).

**Q: Can I share crash files with teammates?**
A: Yes. The `.faultsnap` and `.html` files are fully standalone. You can share them directly with other developers to analyze the crash offline.

**Q: Does FaultSnap send data anywhere?**
A: No. It operates entirely offline. 

### 14. Contributing
Contributions are welcome! Please ensure you run the `pytest` suite before submitting pull requests.

### 15. License
MIT License.
