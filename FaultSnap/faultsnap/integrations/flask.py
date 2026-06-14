import sys
from faultsnap.core import build_crash_data
from faultsnap.storage import save_crash
from faultsnap.config import config

def install(app, **kwargs):
    """
    Install FaultSnap into a Flask application.
    Passes any kwargs to faultsnap.configure().
    """
    from faultsnap.config import configure
    if kwargs:
        configure(**kwargs)

    @app.errorhandler(Exception)
    def faultsnap_flask_handler(error):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        try:
            crash_data = build_crash_data(exc_type, exc_value, exc_traceback)
            filename = save_crash(crash_data)
            print(f"\n[FaultSnap] Flask error captured. Saved to {filename}", file=sys.stderr)
        except Exception as capture_err:
            print(f"\n[FaultSnap] Failed to capture Flask error: {capture_err}", file=sys.stderr)
            
        # Re-raise the error so Flask can handle it normally (e.g. return 500)
        raise error
