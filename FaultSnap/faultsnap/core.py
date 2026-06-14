import os
import sys
import datetime
import platform
import traceback
from faultsnap.config import config, configure
from faultsnap.serializer import summarize
from faultsnap.fingerprint import compute_fingerprint
from faultsnap.mask import is_sensitive_key, mask_value
import json

SAFE_ENV_VARS = {"PATH", "USER", "USERNAME", "HOME", "LANG", "OS", "PWD", "SHELL", "TERM"}

def extract_environment():
    if not config.capture_environment:
        return {}
    
    env_vars = {}
    for k, v in os.environ.items():
        if config.capture_environment == "safe" and k not in SAFE_ENV_VARS:
            continue
            
        if is_sensitive_key(k):
            env_vars[k] = mask_value(v)
        else:
            env_vars[k] = summarize(v)
    return env_vars

def extract_traceback(exc_type, exc_value, exc_traceback):
    frames = []
    
    tb = exc_traceback
    while tb:
        frame = tb.tb_frame
        
        # Serialize locals
        local_vars = {}
        for k, v in frame.f_locals.items():
            if is_sensitive_key(str(k)):
                local_vars[k] = mask_value(v)
            else:
                local_vars[k] = summarize(v)
                
        frames.append({
            "filename": frame.f_code.co_filename,
            "lineno": frame.f_lineno,
            "name": frame.f_code.co_name,
            "locals": local_vars,
        })
        tb = tb.tb_next
        
    extracted = traceback.extract_tb(exc_traceback)
    for i, frame_summary in enumerate(extracted):
        if i < len(frames):
            frames[i]["line"] = frame_summary.line
            
    return frames

def build_crash_data(exc_type, exc_value, exc_traceback):
    timestamp = datetime.datetime.now().isoformat()
    fingerprint = compute_fingerprint(exc_type, exc_value, exc_traceback)
    
    metadata = {
        "timestamp": timestamp,
        "python_version": sys.version,
        "platform": platform.platform(),
        "fingerprint": fingerprint,
        "exception_type": exc_type.__name__ if hasattr(exc_type, '__name__') else str(exc_type),
        "exception_value": str(exc_value),
    }
    
    env_data = extract_environment()
    frames = extract_traceback(exc_type, exc_value, exc_traceback)
    
    exc_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    return {
        "metadata": metadata,
        "environment": env_data,
        "frames": frames,
        "exception_text": exc_text
    }

_original_excepthook = None
_original_threading_excepthook = None
_capsule_writer = None

def faultsnap_hook(exc_type, exc_value, exc_traceback):
    global _original_excepthook, _capsule_writer
    
    try:
        try:
            crash_data = build_crash_data(exc_type, exc_value, exc_traceback)
            
            if _capsule_writer:
                filename = _capsule_writer(crash_data)
                print(f"\n[FaultSnap] Crash captured. Saved to {filename}", file=sys.stderr)
        except Exception as e:
            print(f"\n[FaultSnap] Failed to capture crash: {e}", file=sys.stderr)
    except BaseException:
        # Ultimate fallback so we never crash the hook itself
        print("\n[FaultSnap] Critical internal error while capturing crash. Aborting capture.", file=sys.stderr)
        
    if _original_excepthook:
        _original_excepthook(exc_type, exc_value, exc_traceback)
    else:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

def faultsnap_threading_hook(args):
    """
    args is a threading.ExceptHookArgs object
    """
    global _original_threading_excepthook, _capsule_writer
    
    try:
        try:
            crash_data = build_crash_data(args.exc_type, args.exc_value, args.exc_traceback)
            if _capsule_writer:
                filename = _capsule_writer(crash_data, prefix="crash_thread_")
                print(f"\n[FaultSnap] Thread crash captured. Saved to {filename}", file=sys.stderr)
        except Exception as e:
            print(f"\n[FaultSnap] Failed to capture thread crash: {e}", file=sys.stderr)
    except BaseException:
        print("\n[FaultSnap] Critical internal error while capturing thread crash. Aborting capture.", file=sys.stderr)

    if _original_threading_excepthook:
        _original_threading_excepthook(args)

def install(**kwargs):
    """
    Install FaultSnap into sys.excepthook and threading.excepthook to globally catch unhandled exceptions.
    You can optionally pass configuration overrides here.
    """
    global _original_excepthook, _original_threading_excepthook, _capsule_writer
    
    if kwargs:
        configure(**kwargs)
    
    if sys.excepthook == faultsnap_hook:
        return # Already installed
        
    # Import locally to prevent circular imports
    from faultsnap.storage import save_crash
    _capsule_writer = save_crash
    
    _original_excepthook = sys.excepthook
    sys.excepthook = faultsnap_hook

    # Hook into threading if available (Python 3.8+)
    import threading
    if hasattr(threading, 'excepthook'):
        _original_threading_excepthook = threading.excepthook
        threading.excepthook = faultsnap_threading_hook

def uninstall():
    """
    Uninstall FaultSnap from sys.excepthook and threading.excepthook.
    """
    global _original_excepthook, _original_threading_excepthook
    if sys.excepthook == faultsnap_hook:
        if _original_excepthook:
            sys.excepthook = _original_excepthook
            _original_excepthook = None
        else:
            sys.excepthook = sys.__excepthook__
            
    import threading
    if hasattr(threading, 'excepthook') and threading.excepthook == faultsnap_threading_hook:
        if _original_threading_excepthook:
            threading.excepthook = _original_threading_excepthook
            _original_threading_excepthook = None

# Backwards compatibility for v1.0 initial setup method name
setup = install
