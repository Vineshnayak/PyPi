import sys
from faultsnap.core import build_crash_data
from faultsnap.storage import save_crash
from faultsnap.config import config

def install(app, **kwargs):
    """
    Install FaultSnap into a FastAPI application.
    Passes any kwargs to faultsnap.configure().
    """
    from faultsnap.config import configure
    if kwargs:
        configure(**kwargs)

    @app.exception_handler(Exception)
    async def faultsnap_fastapi_handler(request, exc):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        try:
            crash_data = build_crash_data(exc_type, exc_value, exc_traceback)
            filename = save_crash(crash_data)
            print(f"\n[FaultSnap] FastAPI error captured. Saved to {filename}", file=sys.stderr)
        except Exception as capture_err:
            print(f"\n[FaultSnap] Failed to capture FastAPI error: {capture_err}", file=sys.stderr)
            
        # Re-raise the error so FastAPI's default 500 handler can catch it, or if that fails, Starlette
        raise exc
