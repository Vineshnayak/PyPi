import sys
from faultsnap.core import build_crash_data
from faultsnap.storage import save_crash
from faultsnap.config import config

def install(**kwargs):
    """
    Install FaultSnap into a Streamlit application.
    Since Streamlit catches exceptions internally and doesn't always hit sys.excepthook,
    we patch the internal ScriptRunner.handle_exception method.
    """
    from faultsnap.config import configure
    if kwargs:
        configure(**kwargs)

    try:
        from streamlit.runtime.scriptrunner import ScriptRunner
        
        _original_handle_exception = ScriptRunner.handle_exception
        
        def faultsnap_streamlit_handler(self, e):
            exc_type, exc_value, exc_traceback = sys.exc_info()
            if exc_type is not None:
                try:
                    crash_data = build_crash_data(exc_type, exc_value, exc_traceback)
                    filename = save_crash(crash_data)
                    print(f"\n[FaultSnap] Streamlit error captured. Saved to {filename}", file=sys.stderr)
                except Exception as capture_err:
                    print(f"\n[FaultSnap] Failed to capture Streamlit error: {capture_err}", file=sys.stderr)
            
            # Call original handler
            return _original_handle_exception(self, e)
            
        ScriptRunner.handle_exception = faultsnap_streamlit_handler
        
    except ImportError:
        print("[FaultSnap] Could not install Streamlit integration: streamlit package not found or incompatible version.", file=sys.stderr)
