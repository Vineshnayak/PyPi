import sys
import os
from faultsnap.core import build_crash_data
from faultsnap.storage import save_crash
from faultsnap.config import config

def pytest_exception_interact(node, call, report):
    """
    Pytest hook that is called when an exception is raised which can potentially be interactively handled.
    We use this to capture the crash data.
    """
    if report.failed:
        excinfo = call.excinfo
        if excinfo:
            try:
                # Use default config or overrides if any were set globally
                crash_data = build_crash_data(excinfo.type, excinfo.value, excinfo.tb)
                
                # We put them in a faultsnaps folder by default for tests
                out_dir = os.path.join(config.output_dir, "faultsnaps")
                os.makedirs(out_dir, exist_ok=True)
                
                filename = save_crash(crash_data, prefix="crash_pytest_")
                print(f"\n[FaultSnap] Test failed. Crash captured to {filename}", file=sys.stderr)
            except Exception as e:
                print(f"\n[FaultSnap] Failed to capture test crash: {e}", file=sys.stderr)
