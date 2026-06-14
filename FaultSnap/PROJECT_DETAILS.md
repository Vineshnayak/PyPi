# FaultSnap - Project Details

## Overview
FaultSnap is an offline-first exception capture and diagnostic library for Python. Its primary function is to intercept unhandled exceptions across various Python runtimes, serialize the execution context (call stack, local variables, environment state) safely, and output a portable archive (`.faultsnap`). 

This archive can subsequently be analyzed via command-line utilities or converted into a standalone HTML report.

## System Architecture

FaultSnap is built around a pluggable capture pipeline:

1. **Interception Layer**: Exception hooks are injected at the runtime level (e.g., `sys.excepthook`, `threading.excepthook`, framework middleware).
2. **Context Extraction (`core.py`)**: Traverses the execution frame stack. Extracts `f_locals` from each frame.
3. **Serialization Engine (`serializer.py`)**: Safely evaluates arbitrary Python objects into primitive, JSON-serializable dictionaries. It employs cycle detection, strict length truncation, and robust try-except wrapping to ensure the serialization process itself never raises an exception.
4. **Data Masking (`mask.py`)**: Applies regex-based key matching to strip values associated with sensitive variable names (e.g., "password", "api_key").
5. **Fingerprinting (`fingerprint.py`)**: Generates an SHA-256 hash using the exception type and the traceback sequence (filename, line number, function name) to uniquely identify the *path* of the crash.
6. **Archive Packaging (`capsule.py`)**: Zips the resulting JSON manifest and crash data into a `.faultsnap` archive to minimize disk footprint.
7. **Crash Repository Management (`storage.py`)**: Automatically organizes captured `.faultsnap` archives into a hierarchical repository structure, manages indexing, and enforces retention limits.

## Component Specifications

### 1. Crash Repository Architecture
FaultSnap bypasses root-level file dumps in favor of a structured repository (`FaultSnaps/`):
- **Hierarchy**: `FaultSnaps/<ExceptionType>/<YYYY-MM-DD>/<Fingerprint>/`
- **Artifacts**: Stores the `.faultsnap` capsule, a standalone `.html` report, and a flat `metadata.json`.
- **Indexing (`index.json`)**: Maintains a running catalog of all crashes to enable fast CLI search and statistics without disk traversal.
- **Latest Pointer**: Automatically maintains a `FaultSnaps/latest/` directory containing the most recent crash.
- **Retention Policies**: Configurable limits (`max_reports_per_fingerprint` and `max_days_to_keep`) automatically purge expired crash data on a continuous basis.

### 2. Supported Runtimes & Frameworks
FaultSnap supports standard synchronous execution via `sys.excepthook`. It extends support to background contexts and external frameworks via specific patches:
- **Threads**: Intercepts via `threading.excepthook`.
- **AsyncIO**: Intercepts via the active event loop's exception handler.
- **Multiprocessing**: Monkey-patches `multiprocessing.Process.run` to ensure child worker crashes are captured.
- **Web Frameworks**: Middleware integrations for Django, Flask, FastAPI, and Streamlit intercept the request lifecycle prior to standard framework error handling.
- **Testing**: A Pytest plugin intercepts test failures natively.

### 3. Serialization Safeguards
Arbitrary object serialization in a crash context is highly volatile. FaultSnap mitigates memory exhaustion and cascading crashes through several mechanisms:
- **Depth Limits**: Traversal stops at a configurable depth (`max_depth=5`).
- **Global Item Limits**: A persistent counter across the recursive traversal caps the total number of objects processed (`max_total_items=10000`).
- **Iteration Limits**: Lists and dictionaries are truncated after a threshold (`max_items=50`).
- **Circular Reference Protection**: Object IDs are tracked. If a cycle is detected, the traversal halts and logs a `<CircularReference>` placeholder.
- **`__dict__` and `__slots__` fallback**: Custom objects are serialized by their explicit data structures. If attribute access triggers an internal failure, a `<Exception in repr>` fallback is provided.

## Command-Line Interface (CLI)
The CLI (`faultsnap/cli.py`) utilizes the `rich` library to present structured crash data.
Commands:
- `list`: Shows all stored crashes in a tabular format read from `index.json`.
- `latest`: Automatically inspects the crash within `FaultSnaps/latest/`.
- `search`: Filters the crash index by exception type or fingerprint.
- `stats`: Displays repository aggregates (total crashes, unique fingerprints, oldest/newest).
- `clean`: Manually triggers the retention purge process.
- `inspect`: Displays the manifest and raw exception traceback.
- `stack`: Renders a tree view of the call stack.
- `vars`: Iterates over the call stack and renders tables of local variables per frame.
- `env`: Renders captured environment variables.
- `fingerprint`: Outputs the SHA-256 hash.
- `diff`: Performs a comparative analysis of two manifest files.
- `html`: Invokes the Jinja2 HTML generator.

## HTML Report Generator
The HTML generator (`faultsnap/html.py` & `faultsnap/templates/html_report.py`) utilizes `jinja2` to render an interactive diagnostic dashboard.
- Generates reports adjacent to their corresponding `.faultsnap` capsules.
- Uses `Environment(autoescape=True)` to prevent cross-site scripting (XSS) via injected variable payloads.
- Bundles `mermaid.min.js` locally to ensure the execution graph renders securely and entirely offline.
- Implements client-side JavaScript for variable filtering and searching.

## Security Posture
1. **Offline Only**: Operates without external API dependencies or telemetry. 
2. **Auto-escaping**: Strict HTML output escaping.
3. **Environment Filtering**: Defaults to `capture_environment="safe"`, which explicitly allow-lists generic OS variables (`PATH`, `OS`, `TERM`) while dropping everything else, mitigating accidental credential leaks via `os.environ`.
4. **Regex Masking**: Keys like `SECRET`, `KEY`, `PASS`, `TOKEN`, `AUTH` trigger immediate value redaction.

## Performance Profile
Based on automated benchmarks:
- **Overhead**: Processing a 10,000-item nested dataset takes approximately ~30ms on modern hardware.
- **Disk I/O**: The `.faultsnap` ZIP compression averages ~10ms for standard crash traces, producing archives typically under 50KB.
- **Cleanup**: Retention purging evaluates `index.json` linearly, ensuring minimal runtime impact.

## Testing
The `pytest` test suite validates:
- OOM protection and recursion limits.
- Circular dependency resolution.
- Secret masking algorithms.
- Custom object `__dict__`/`__slots__` serialization.
- Exception handling when `.faultsnap` files are intentionally corrupted or missing internal JSON payloads (`CapsuleCorruptedError`).
