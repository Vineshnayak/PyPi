import sys
import os
import multiprocessing
from faultsnap.core import build_crash_data
from faultsnap.storage import save_crash
from faultsnap.config import config

_original_process_run = None

def faultsnap_process_run(self):
    """
    Monkey-patched multiprocessing.Process.run method.
    """
    try:
        if _original_process_run:
            _original_process_run(self)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        try:
            crash_data = build_crash_data(exc_type, exc_value, exc_traceback)
            
            # Make the filename specific to the worker PID so they don't overwrite
            output_dir = config.output_dir
            pid = os.getpid()
            
            # We bypass _capsule_writer caching since we are in a new process
            filename = save_crash(crash_data, prefix=f"crash_worker_{pid}_")
            print(f"\n[FaultSnap] Multiprocessing worker (PID {pid}) crash captured. Saved to {filename}", file=sys.stderr)
        except Exception as capture_err:
            print(f"\n[FaultSnap] Failed to capture multiprocessing worker crash: {capture_err}", file=sys.stderr)
        except BaseException:
            print("\n[FaultSnap] Critical internal error while capturing worker crash. Aborting capture.", file=sys.stderr)
            
        raise

def install(**kwargs):
    """
    Install FaultSnap into the multiprocessing module to capture crashes in child processes.
    Monkey-patches multiprocessing.Process.run.
    """
    global _original_process_run
    
    from faultsnap.config import configure
    if kwargs:
        configure(**kwargs)
        
    if _original_process_run is None:
        _original_process_run = multiprocessing.Process.run
        multiprocessing.Process.run = faultsnap_process_run
